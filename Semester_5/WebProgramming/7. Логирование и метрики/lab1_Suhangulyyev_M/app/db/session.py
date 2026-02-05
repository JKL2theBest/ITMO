from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings

Base = declarative_base()  # Класс "базы" для всех ORM
# Все модели (User, News, Comment) будут наследоваться от этого Base.

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DB_ECHO_LOG)
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
