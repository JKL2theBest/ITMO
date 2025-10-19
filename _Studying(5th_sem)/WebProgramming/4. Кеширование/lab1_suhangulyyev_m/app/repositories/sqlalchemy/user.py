from sqlalchemy import select
from app.models.user import User
from app.repositories.sqlalchemy.base import SQLAlchemyRepository
from app.schemas.user import UserCreate, UserUpdate


class UserRepository(SQLAlchemyRepository[User, UserCreate, UserUpdate]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        query = select(self.model).where(self.model.email == email)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_multi(self, skip: int = 0, limit: int = 100) -> list[User]:
        query = select(self.model).order_by(self.model.name).offset(skip).limit(limit)
        if self._load_options:
            query = query.options(*self._load_options)
        result = await self.session.execute(query)
        return result.scalars().all()
