"""
Модуль для настройки и управления подключением к базе данных.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import settings
from db.models import Base

# Создание асинхронного "движка" SQLAlchemy на основе URL из конфигурации.
# echo=True полезно для отладки, т.к. выводит все SQL-запросы в консоль.
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Создание фабрики асинхронных сессий. Эта фабрика будет производить
# объекты сессий, когда нам понадобится связаться с БД.
AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Важно для асинхронного кода
)


async def get_session() -> AsyncSession:
    """
    Фабричная функция для предоставления сессии базы данных.

    Предназначена для использования в качестве зависимости, обеспечивая
    каждую операцию собственной сессией.
    """
    async with AsyncSessionFactory() as session:
        return session


async def init_db():
    """
    Инициализирует базу данных.

    Асинхронно создает все таблицы, определенные в метаданных Base,
    если они еще не существуют в базе данных.
    """
    async with engine.begin() as conn:
        # В реальном проекте здесь бы использовались миграции (например, Alembic),
        # но для лабораторной работы достаточно create_all.
        await conn.run_sync(Base.metadata.create_all)
