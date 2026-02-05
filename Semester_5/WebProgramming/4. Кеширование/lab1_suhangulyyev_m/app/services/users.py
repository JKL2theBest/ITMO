import uuid
from fastapi import HTTPException, status
from redis.asyncio import Redis
from app.repositories.sqlalchemy.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.models.user import User
from app.services.base import BaseService
from app.core.security import hash_password
import logging

logger = logging.getLogger(__name__)


class UserService(BaseService):
    _cache_ttl = 300  # 5 минут

    def __init__(self, user_repo: UserRepository, redis_client: Redis):
        super().__init__(user_repo, redis_client)
        self.repository: UserRepository

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Получение пользователя по ID с кэшированием."""
        cache_key = f"user:{user_id}"
        if cached_user := await self.redis.get(cache_key):
            logger.info(f"User {user_id} found in cache.")
            # Десериализуем из JSON в Pydantic модель, а затем создаем ORM-объект
            # Это компромисс, чтобы get_current_user возвращал ORM-модель
            user_data = UserResponse.model_validate_json(cached_user)
            return User(**user_data.model_dump())

        logger.info(f"User {user_id} not in cache, fetching from DB.")
        db_user = await self.repository.get_by_id(user_id)

        if not db_user:
            # Для get_current_user важно вернуть именно None
            return None

        user_to_cache = UserResponse.model_validate(db_user)
        await self.redis.set(
            cache_key, user_to_cache.model_dump_json(), ex=self._cache_ttl
        )
        return db_user

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
        """Обновление пользователя с инвалидацией кэша."""
        updated_user = await self.repository.update(
            db_obj=user_to_update, update_data=user_data
        )
        await self.redis.delete(f"user:{updated_user.id}")
        logger.info(f"Cache for user {updated_user.id} invalidated.")
        return updated_user

    async def delete_user(self, user_id: uuid.UUID) -> None:
        """Удаление пользователя с инвалидацией кэша."""
        user_to_delete = await self.get_by_id(user_id)  # проверить существование
        await self.repository.delete(db_obj=user_to_delete)
        await self.redis.delete(f"user:{user_id}")
        logger.info(f"Cache for user {user_id} invalidated.")
