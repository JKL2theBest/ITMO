from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.schemas.user import UserCreateInternal


class UserRepository:
    """
    Слой доступа к данным (Repository) для таблицы 'users'.
    Инкапсулирует всю логику прямого взаимодействия с БД (SQL-запросы).
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_login(self, login: str) -> User | None:
        """Находит пользователя по логину."""
        query = select(User).where(User.login == login)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def create(self, user_data: UserCreateInternal) -> User:
        """
        Создает новую запись пользователя в БД.
        """
        new_user = User(login=user_data.login, password_hash=user_data.password_hash)
        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)
        return new_user
