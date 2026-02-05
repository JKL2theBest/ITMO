import uuid
from fastapi import HTTPException, status
from app.repositories.sqlalchemy.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User
from app.services.base import BaseService


class UserService(BaseService):
    def __init__(self, user_repo: UserRepository):
        super().__init__(user_repo)

    async def create_user(self, user_data: UserCreate) -> User:
        if await self.repository.get_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )
        return await self.repository.create(user_data)

    async def update_user(self, user_id: uuid.UUID, user_data: UserUpdate) -> User:
        user_to_update = await self.get_by_id(user_id)
        return await self.repository.update(
            db_obj=user_to_update, update_data=user_data
        )

    async def delete_user(self, user_id: uuid.UUID) -> None:
        user_to_delete = await self.get_by_id(user_id)
        await self.repository.delete(db_obj=user_to_delete)
