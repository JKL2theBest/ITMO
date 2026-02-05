"""
Модуль слоя доступа к данным (Repository).

Инкапсулирует всю логику взаимодействия с базой данных, предоставляя
высокоуровневые методы для работы с сущностями.
"""

from typing import Optional, List
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Role, User


class UserRepository:
    """Репозиторий для выполнения CRUD-операций с моделью User."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Находит пользователя по имени пользователя.

        Выполняет "жадную" загрузку связанной роли (eager loading), чтобы
        избежать дополнительных запросов к БД при доступе к user.role.

        Args:
            username: Имя пользователя для поиска.

        Returns:
            Объект User, если найден, иначе None.
        """
        stmt = (
            select(User)
            .where(User.username == username)
            .options(selectinload(User.role))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(
        self, username: str, hashed_password: str, role: Role
    ) -> User:
        """Создает нового пользователя в базе данных."""
        new_user = User(username=username, hashed_password=hashed_password, role=role)
        self.session.add(new_user)
        # flush отправляет SQL в БД, но не завершает транзакцию.
        # Это позволяет получить, например, ID нового объекта.
        await self.session.flush()
        await self.session.refresh(new_user, attribute_names=["role"])
        return new_user

    async def update_user(self, user: User) -> User:
        """
        Обновляет данные пользователя.

        Так как мы работаем с объектом, который уже находится в сессии,
        изменения его атрибутов отслеживаются SQLAlchemy. `flush` отправит
        UPDATE-запрос в БД.

        Args:
            user: Объект User с измененными данными.

        Returns:
            Обновленный объект User.
        """
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Находит пользователя по его UUID."""
        stmt = select(User).where(User.id == user_id).options(selectinload(User.role))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class RoleRepository:
    """Репозиторий для выполнения операций с моделью Role."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_name(self, name: str) -> Optional[Role]:
        """Находит роль по названию."""
        stmt = select(Role).where(Role.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_role(self, name: str) -> Role:
        """Создает новую роль."""
        new_role = Role(name=name)
        self.session.add(new_role)
        await self.session.flush()
        await self.session.refresh(new_role)
        return new_role

    async def get_all(self) -> List[Role]:
        """Возвращает список всех ролей в системе."""
        stmt = select(Role)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
