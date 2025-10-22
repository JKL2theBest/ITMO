"""
Модуль слоя бизнес-логики для аутентификации и авторизации.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from core.security import hash_password, verify_password
from db.repository import RoleRepository, UserRepository
from db.models import User
from schemas.user_schemas import UserCreate, UserPublic
from services.session_service import SessionService
from .mfa_service import MFAService


class AuthService:
    """
    Сервис, инкапсулирующий логику регистрации и аутентификации.
    """

    def __init__(self, session: AsyncSession):
        self.user_repo = UserRepository(session)
        self.role_repo = RoleRepository(session)
        self.session_service = SessionService(session)
        self.mfa_service = MFAService()
        self.session = session

    async def register_user(self, user_data: UserCreate) -> UserPublic:
        """
        Регистрирует нового пользователя в системе.

        1. Проверяет, не занято ли имя пользователя.
        2. Хеширует пароль.
        3. Находит или создает роль пользователя.
        4. Создает пользователя через репозиторий.
        5. Возвращает публичные данные пользователя.

        Args:
            user_data: Данные для создания пользователя (схема UserCreate).

        Returns:
            Публичные данные созданного пользователя (схема UserPublic).

        Raises:
            ValueError: Если пользователь с таким именем уже существует.
        """
        existing_user = await self.user_repo.get_by_username(user_data.username)
        if existing_user:
            raise ValueError(f"Username '{user_data.username}' is already taken.")

        hashed_pass = hash_password(user_data.password)

        role = await self.role_repo.get_by_name(user_data.role_name)
        if not role:
            # Если роль не найдена, создаем ее.
            role = await self.role_repo.create_role(user_data.role_name)

        new_user = await self.user_repo.create_user(
            username=user_data.username,
            hashed_password=hashed_pass,
            role=role,
        )

        # Собираем публичную модель из объекта SQLAlchemy
        return UserPublic(
            id=new_user.id,
            username=new_user.username,
            role_name=new_user.role.name,
            created_at=new_user.created_at,
        )

    async def authenticate_user(
        self, username: str, password: str
    ) -> tuple[User | None, bool]:
        """
        Аутентифицирует пользователя.

        1. Находит пользователя по имени.
        2. Сравнивает хеш предоставленного пароля с хешем из БД.
        3. В случае успеха генерирует и возвращает токен сессии.

        Args:
            username: Имя пользователя.
            password: Пароль в открытом виде.

        Returns:
            возвращает кортеж (пользователь, требуется_ли_mfa).

        Raises:
            ValueError: Если аутентификация не удалась (неверное имя или пароль).
        """
        user = await self.user_repo.get_by_username(username)

        if not user or not verify_password(password, user.hashed_password):
            raise ValueError("Invalid username or password.")

        # Возвращаем пользователя и флаг необходимости второго фактора
        return user, user.is_mfa_enabled

    async def authorize(self, token: str, required_role: str) -> bool:
        """
        Проверяет права доступа пользователя по токену сессии.

        1. Находит пользователя по токену сессии.
        2. Сравнивает роль пользователя с требуемой.

        Args:
            token: Токен сессии для проверки.
            required_role: Название требуемой роли (например, 'admin').

        Returns:
            True, если пользователь авторизован и имеет нужную роль, иначе False.
        """
        user = await self.session_service.get_user_by_token(token)

        if not user:
            return False  # Пользователь не найден или сессия истекла

        # Простая проверка по названию роли.
        # В более сложных системах здесь может быть проверка иерархии ролей
        # или отдельных прав (permissions).
        return user.role.name == required_role

    async def change_password(
        self, token: str, old_password: str, new_password: str
    ) -> bool:
        """
        Изменяет пароль аутентифицированного пользователя.

        1. Находит пользователя по токену сессии.
        2. Проверяет, что старый пароль введен верно.
        3. Хеширует новый пароль и обновляет запись в БД.

        Args:
            token: Токен текущей сессии пользователя.
            old_password: Текущий пароль для проверки.
            new_password: Новый пароль.

        Returns:
            True в случае успешной смены пароля.

        Raises:
            ValueError: Если пользователь не найден, старый пароль неверный,
                        или новый пароль совпадает со старым.
        """
        user = await self.session_service.get_user_by_token(token)
        if not user:
            raise ValueError("Invalid session or user not found.")

        if not verify_password(old_password, user.hashed_password):
            raise ValueError("Incorrect old password.")

        if old_password == new_password:
            raise ValueError("New password cannot be the same as the old password.")

        # Все проверки пройдены, обновляем пароль
        user.hashed_password = hash_password(new_password)
        await self.user_repo.update_user(user)

        return True
