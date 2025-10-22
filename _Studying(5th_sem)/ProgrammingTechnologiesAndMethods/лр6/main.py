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


async def handle_login(service: AuthService):
    """Обрабатывает команду входа в систему."""
    global current_session_token
    print("\n--- Вход в систему ---")
    username = input("Имя пользователя: ")
    password = getpass("Пароль: ")

    try:
        token = await service.authenticate_user(username, password)
        current_session_token = token
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


async def main():
    """Главная функция, запускающая цикл приложения."""
    print("Инициализация базы данных...")
    await init_db()
    print("Система аутентификации готова к работе.")

    session: AsyncSession = AsyncSessionFactory()
    auth_service = AuthService(session)
    session_service = SessionService(session)

    try:
        while True:
            print("\n" + "=" * 30)
            print("Доступные команды:")
            print("  register - зарегистрировать нового пользователя")
            print("  login    - войти в систему")
            print("  logout   - выйти из системы")
            print("  access <resource_name> - получить доступ к ресурсу")
            print("    (доступные ресурсы: common_resource, admin_resource)")
            print("  exit     - выйти из программы")
            print("=" * 30)

            # Эта строка теперь находится внутри блока try
            command_line = input("> ").strip().lower().split()
            if not command_line:
                continue

            command = command_line[0]

            if command == "register":
                await handle_register(auth_service)
                await session.commit()
            elif command == "login":
                await handle_login(auth_service)
                await session.commit()
            elif command == "logout":
                await handle_logout(session_service)
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
