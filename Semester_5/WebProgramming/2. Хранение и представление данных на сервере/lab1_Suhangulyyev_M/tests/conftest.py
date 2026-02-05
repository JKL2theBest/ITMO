import asyncio
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from alembic import command
from alembic.config import Config
from app.core.config import settings
from app.db.session import get_db_session
from app.main import app

# --- НАСТРОЙКА ТЕСТОВОЙ БД ---

TEST_DATABASE_URL = f"{settings.DATABASE_URL}_test"

engine_test = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
async_session_maker = async_sessionmaker(
    engine_test, class_=AsyncSession, expire_on_commit=False
)

# --- ФИКСТУРА ДЛЯ СОЗДАНИЯ И ОЧИСТКИ БД ---


@pytest.fixture(scope="function", autouse=True)
def apply_migrations():
    sync_engine = create_engine(
        settings.DATABASE_URL.replace("+asyncpg", "+psycopg2"), echo=False
    )
    db_name = TEST_DATABASE_URL.split("/")[-1]

    with sync_engine.connect() as conn:
        conn.execute(text("COMMIT"))
        conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
        conn.execute(text("COMMIT"))
        conn.execute(text(f"CREATE DATABASE {db_name}"))
        conn.execute(text("COMMIT"))

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option(
        "sqlalchemy.url", TEST_DATABASE_URL.replace("+asyncpg", "+psycopg2")
    )
    command.upgrade(alembic_cfg, "7c771bba3ad7")  # Спорно, но пусть будет

    yield

    with sync_engine.connect() as conn:
        conn.execute(text("COMMIT"))
        conn.execute(text(f"DROP DATABASE {db_name}"))
        conn.execute(text("COMMIT"))


# --- ФИКСТУРА ДЛЯ СОЗДАНИЯ ТЕСТОВОГО КЛИЕНТА API ---


@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_maker() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_async_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# --- ФИКСТУРА ДЛЯ АСИНХРОННОГО EVENT LOOP (для pytest-asyncio) ---


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
