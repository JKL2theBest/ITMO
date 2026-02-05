from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL)

AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Зависимость FastAPI для получения сессии базы данных.
    """
    async with AsyncSessionLocal() as session:
        yield session
