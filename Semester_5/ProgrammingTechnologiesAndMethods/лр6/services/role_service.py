"""
Модуль бизнес-логики для управления ролями пользователей.
"""

from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from db.repository import RoleRepository, UserRepository
from schemas.user_schemas import UserPublic


class RoleService:
    """Сервис для управления ролями."""

    def __init__(self, session: AsyncSession):
        self.role_repo = RoleRepository(session)
        self.user_repo = UserRepository(session)

    async def list_roles(self) -> List[str]:
        """Возвращает список названий всех ролей."""
        roles = await self.role_repo.get_all()
        return [role.name for role in roles]

    async def create_role(self, role_name: str) -> str:
        """
        Создает новую роль.

        Raises:
            ValueError: если роль с таким именем уже существует.
        """
        existing_role = await self.role_repo.get_by_name(role_name)
        if existing_role:
            raise ValueError(f"Role '{role_name}' already exists.")

        new_role = await self.role_repo.create_role(role_name)
        return new_role.name

    async def assign_role_to_user(self, username: str, role_name: str) -> UserPublic:
        """
        Назначает новую роль пользователю.

        Raises:
            ValueError: если пользователь или роль не найдены.
        """
        user = await self.user_repo.get_by_username(username)
        if not user:
            raise ValueError(f"User '{username}' not found.")

        role = await self.role_repo.get_by_name(role_name)
        if not role:
            raise ValueError(f"Role '{role_name}' not found.")

        user.role = role
        updated_user = await self.user_repo.update_user(user)

        return UserPublic(
            id=updated_user.id,
            username=updated_user.username,
            role_name=updated_user.role.name,
            created_at=updated_user.created_at,
        )
