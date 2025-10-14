import uuid
from fastapi import HTTPException, status
from app.repositories.sqlalchemy.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User
from app.services.base import BaseService
from app.core.security import hash_password


class UserService(BaseService):
    def __init__(self, user_repo: UserRepository):
        super().__init__(user_repo)

    async def create_user(self, user_data: UserCreate) -> User:
        if await self.repository.get_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )
        user_data_dict = user_data.model_dump(exclude={"password"})
        hashed_pass = hash_password(user_data.password)

        db_obj = self.repository.model(**user_data_dict, hashed_password=hashed_pass)

        self.repository.session.add(db_obj)
        await self.repository.session.commit()
        await self.repository.session.refresh(db_obj)
        return db_obj

    async def update_user(self, user_to_update: User, user_data: UserUpdate) -> User:
        return await self.repository.update(
            db_obj=user_to_update, update_data=user_data
        )

    async def delete_user(self, user_id: uuid.UUID) -> None:
        user_to_delete = await self.get_by_id(user_id)
        await self.repository.delete(db_obj=user_to_delete)
