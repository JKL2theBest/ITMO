"""
Основной модуль приложения.

Точка входа для запуска консольного интерфейса системы
аутентификации и авторизации.
"""

import asyncio
from getpass import getpass

from sqlalchemy.ext.asyncio import AsyncSession

from db.database import AsyncSessionFactory, init_db
from schemas.user_schemas import UserCreate
from services.auth_service import AuthService
from services.session_service import SessionService
from services.role_service import RoleService

# --- "Защищенные" ресурсы нашего приложения ---
PROTECTED_DATA = {
    "common_resource": "Это общедоступные данные для всех вошедших пользователей.",
    "admin_resource": "Это секретные данные, доступные только администратору!",
}

# --- Глобальное состояние сессии ---
# В реальном приложении это состояние управлялось бы более сложно,
# но для консольного UI это приемлемое упрощение.
current_session_token: str | None = None


async def handle_register(service: AuthService):
    """Обрабатывает команду регистрации."""
    print("\n--- Регистрация нового пользователя ---")
    username = input("Введите имя пользователя: ")
    password = getpass("Введите пароль: ")
    role_name = input("Введите роль (user/admin) [user]: ") or "user"

    try:
        user_data = UserCreate(
            username=username, password=password, role_name=role_name
        )
        new_user = await service.register_user(user_data)
        print(
            f"\n[OK] Пользователь '{new_user.username}' успешно создан с ролью '{new_user.role_name}'."
        )
    except ValueError as e:
        print(f"\n[Ошибка] {e}")


async def handle_enable_mfa(auth_service: AuthService, role_service: RoleService):
    """Включает MFA для пользователя."""
    print("\n--- Включение MFA для пользователя ---")
    username = input("Введите имя пользователя, для которого нужно включить MFA: ")

    user_model = await auth_service.user_repo.get_by_username(username)
    if not user_model:
        print(f"\n[Ошибка] Пользователь '{username}' не найден.")
        return

    if user_model.is_mfa_enabled:
        print(f"\n[Инфо] MFA уже включен для пользователя '{username}'.")
        return

    secret = auth_service.mfa_service.generate_secret()
    user_model.mfa_secret = secret
    user_model.is_mfa_enabled = True
    await auth_service.user_repo.update_user(user_model)

    uri = auth_service.mfa_service.get_provisioning_uri(username, secret)
    print("\n[OK] MFA успешно включен!")
    print("---------------------------------------------------------")
    print("Секретный ключ (сохраните его!):", secret)
    print("Откройте эту ссылку в браузере, чтобы увидеть QR-код для сканирования:")
    print(f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={uri}")
    print("---------------------------------------------------------")


async def handle_login(auth_service: AuthService, session_service: SessionService):
    """Обрабатывает команду входа в систему (с поддержкой MFA)."""
    global current_session_token
    print("\n--- Вход в систему ---")
    username = input("Имя пользователя: ")
    password = getpass("Пароль: ")

    try:
        # Шаг 1: Проверка имени и пароля
        user, mfa_required = await auth_service.authenticate_user(username, password)

        # Шаг 2: Если требуется, проверяем второй фактор (TOTP)
        if mfa_required:
            mfa_code = input("Введите 6-значный код из приложения-аутентификатора: ")
            if not user.mfa_secret or not auth_service.mfa_service.verify_code(
                user.mfa_secret, mfa_code
            ):
                print("\n[Ошибка] Неверный код аутентификации.")
                return

        # Шаг 3: Создание сессии
        new_session = await session_service.create_session(user)
        current_session_token = new_session.token
        print("\n[OK] Вход выполнен успешно. Сессия открыта.")

    except ValueError as e:
        print(f"\n[Ошибка] {e}")


async def handle_logout(service: SessionService):
    """Обрабатывает команду выхода."""
    global current_session_token
    if not current_session_token:
        print("\n[Инфо] Вы не вошли в систему.")
        return

    success = await service.terminate_session(current_session_token)
    if success:
        current_session_token = None
        print("\n[OK] Выход выполнен. Сессия завершена.")
    else:
        print("\n[Ошибка] Не удалось завершить сессию (возможно, она уже истекла).")


async def handle_access_resource(service: AuthService, resource_name: str):
    """Обрабатывает команду доступа к ресурсу."""
    if not current_session_token:
        print("\n[Ошибка] Доступ запрещен. Пожалуйста, войдите в систему.")
        return

    if resource_name not in PROTECTED_DATA:
        print(f"\n[Ошибка] Ресурс '{resource_name}' не найден.")
        return

    # Авторизация: определяем, какая роль нужна для доступа
    required_role = "admin" if resource_name == "admin_resource" else "user"

    is_authorized = await service.authorize(current_session_token, required_role)

    if is_authorized or (
        required_role == "user"
        and await service.authorize(current_session_token, "admin")
    ):
        # Условие выше реализует простую иерархию: админ имеет доступ ко всему,
        # к чему имеет доступ обычный пользователь.
        print(f"\n[OK] Доступ к '{resource_name}' разрешен.")
        print(f"Содержимое: {PROTECTED_DATA[resource_name]}")
    else:
        print(f"\n[Ошибка] Доступ к '{resource_name}' запрещен. Недостаточно прав.")


async def handle_change_password(service: AuthService):
    """Обрабатывает команду смены пароля."""
    if not current_session_token:
        print("\n[Ошибка] Операция невозможна. Пожалуйста, войдите в систему.")
        return

    print("\n--- Смена пароля ---")
    old_password = getpass("Введите старый пароль: ")
    new_password = getpass("Введите новый пароль: ")
    confirm_password = getpass("Подтвердите новый пароль: ")

    if new_password != confirm_password:
        print("\n[Ошибка] Новые пароли не совпадают.")
        return

    try:
        success = await service.change_password(
            current_session_token, old_password, new_password
        )
        if success:
            print("\n[OK] Пароль успешно изменен.")
    except ValueError as e:
        print(f"\n[Ошибка] {e}")


# --- функции-обработчики для админа ---


async def handle_list_roles(role_service: RoleService):
    """Выводит список всех ролей."""
    print("\n--- Список ролей ---")
    roles = await role_service.list_roles()
    if not roles:
        print("В системе нет созданных ролей.")
    else:
        for role_name in roles:
            print(f"- {role_name}")


async def handle_create_role(role_service: RoleService):
    """Создает новую роль."""
    print("\n--- Создание новой роли ---")
    role_name = input("Введите название новой роли: ").strip().lower()
    if not role_name:
        print("\n[Ошибка] Название роли не может быть пустым.")
        return
    try:
        new_role = await role_service.create_role(role_name)
        print(f"\n[OK] Роль '{new_role}' успешно создана.")
    except ValueError as e:
        print(f"\n[Ошибка] {e}")


async def handle_assign_role(role_service: RoleService):
    """Назначает роль пользователю."""
    print("\n--- Назначение роли пользователю ---")
    username = input("Введите имя пользователя: ")
    role_name = input("Введите название новой роли: ")
    try:
        updated_user = await role_service.assign_role_to_user(username, role_name)
        print(
            f"\n[OK] Пользователю '{updated_user.username}' назначена роль '{updated_user.role_name}'."
        )
    except ValueError as e:
        print(f"\n[Ошибка] {e}")


async def main():
    """Главная функция, запускающая цикл приложения."""
    print("Инициализация базы данных...")
    await init_db()
    print("Система аутентификации готова к работе.")

    session: AsyncSession = AsyncSessionFactory()
    auth_service = AuthService(session)
    session_service = SessionService(session)
    role_service = RoleService(session)

    try:
        while True:
            print("\n" + "=" * 30)
            print("Доступные команды:")
            print("  register - зарегистрировать нового пользователя")
            print("  login    - войти в систему")
            print("  logout   - выйти из системы")
            print("  chpasswd - сменить пароль")
            print("  access <resource_name> - получить доступ к ресурсу")
            print("    (доступные ресурсы: common_resource, admin_resource)")
            print("  exit     - выйти из программы")
            print("\n  --- Команды администратора ---")
            print(
                "  enable_mfa          - включить MFA для пользователя (только админ)"
            )
            print("  list_roles        - показать все роли")
            print("  create_role       - создать новую роль")
            print("  assign_role       - назначить роль пользователю")
            print("=" * 30)

            command_line = input("> ").strip().lower().split()

            if not command_line:
                continue

            command = command_line[0]

            if command in ["list_roles", "create_role", "assign_role", "enable_mfa"]:
                is_admin = await auth_service.authorize(current_session_token, "admin")
                if not is_admin:
                    print("\n[Ошибка] Доступ запрещен. Требуются права администратора.")
                    continue

                if command == "list_roles":
                    await handle_list_roles(role_service)
                elif command == "create_role":
                    await handle_create_role(role_service)
                elif command == "assign_role":
                    await handle_assign_role(role_service)
                elif command == "enable_mfa":
                    await handle_enable_mfa(auth_service, role_service)

                await session.commit()
                # `continue` пропускает все остальные elif/else и начинает цикл заново
                continue

            elif command == "register":
                await handle_register(auth_service)
                await session.commit()
            elif command == "login":
                await handle_login(auth_service, session_service)
                await session.commit()
            elif command == "logout":
                await handle_logout(session_service)
                await session.commit()
            elif command == "chpasswd":
                await handle_change_password(auth_service)
                await session.commit()
            elif command == "access":
                if len(command_line) > 1:
                    await handle_access_resource(auth_service, command_line[1])
                else:
                    print(
                        "\n[Ошибка] Укажите имя ресурса (например, 'access common_resource')."
                    )
            elif command == "exit":
                if current_session_token:
                    await handle_logout(session_service)
                    await session.commit()  # Не забываем закоммитить выход
                print("Завершение работы.")
                break
            else:
                print(f"\n[Ошибка] Неизвестная команда: '{command}'")
    finally:
        # Этот блок выполнится при выходе из цикла (через break) или при ошибке
        await session.close()
        print("Соединение с БД закрыто.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nПрограмма прервана пользователем.")
