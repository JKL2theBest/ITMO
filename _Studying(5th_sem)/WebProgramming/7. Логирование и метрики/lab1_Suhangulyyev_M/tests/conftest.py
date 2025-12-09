import os
import shutil
import tempfile
import asyncio
import uuid
from typing import AsyncGenerator

# Настройка окружения ДО импорта app.main
TEST_METRICS_DIR = tempfile.mkdtemp()
os.environ["PROMETHEUS_MULTIPROC_DIR"] = TEST_METRICS_DIR

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, text
from sqlalchemy.engine import create_engine as create_sync_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from fastapi import FastAPI
from redis.asyncio import Redis as AsyncRedis
from fakeredis import aioredis as fake_aioredis

from alembic import command
from alembic.config import Config

from app.core.config import settings
from app.db.cache import get_redis_client
from app.db.session import get_db_session
from app.main import app
from app.models.user import User
from app.schemas.role import UserRole

# --- Настройка БД и миграций ---

engine_test = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
async_session_maker = async_sessionmaker(
    engine_test, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Цикл обработки событий в рамках сеанса."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """Применяет миграции один раз за сеанс тестирования и чистит метрики."""
    # 1. Настройка БД
    config = Config("alembic.ini")
    sync_engine = create_sync_engine(settings.SYNC_DATABASE_URL)
    with sync_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    command.upgrade(config, "head")

    yield

    # 2. Очистка после тестов
    with sync_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    sync_engine.dispose()

    # 3. Удаление временной папки с метриками
    if os.path.exists(TEST_METRICS_DIR):
        shutil.rmtree(TEST_METRICS_DIR, ignore_errors=True)


# --- Фикстуры приложения и клиента ---


@pytest_asyncio.fixture(scope="function")
async def test_redis() -> AsyncGenerator[AsyncRedis, None]:
    """Фикстура, создающая фейковый клиент Redis для тестов."""
    client = fake_aioredis.FakeRedis(decode_responses=True)
    yield client
    await client.flushall()
    await client.aclose()


@pytest_asyncio.fixture(scope="function")
async def test_app(test_redis: AsyncRedis) -> AsyncGenerator[FastAPI, None]:
    """Фикстура для создания экземпляра тестового приложения с переопределенными зависимостями."""

    async def override_get_db_session():
        async with async_session_maker() as session:
            yield session

    async def override_get_redis_client():
        yield test_redis

    # Отключаем lifespan для тестов, так как он пытается создать реальный пул соединений
    app.router.lifespan_context = None

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_redis_client] = override_get_redis_client
    yield app
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Фикстура для неавторизованного HTTP клиента."""
    async with ASGITransport(app=test_app) as transport:
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


@pytest_asyncio.fixture(scope="function")
async def db_session_test() -> AsyncGenerator[AsyncSession, None]:
    """Фикстура для прямого получения сессии для тестов."""
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def user_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Фикстура для авторизованного клиента USER."""
    async with ASGITransport(app=test_app) as transport:
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            user_data = {
                "name": "Test User",
                "email": f"{uuid.uuid4()}@test.com",
                "password": "password123",
            }
            register_response = await c.post("/api/v1/auth/register", json=user_data)
            assert register_response.status_code == 201, register_response.text

            login_response = await c.post(
                "/api/v1/auth/login",
                data={
                    "username": user_data["email"],
                    "password": user_data["password"],
                },
            )
            tokens = login_response.json()
            c.headers["Authorization"] = f"Bearer {tokens['access_token']}"
            c.user_data = register_response.json()
            c.refresh_token = tokens["refresh_token"]
            yield c


@pytest_asyncio.fixture(scope="function")
async def author_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Фикстура для авторизованного клиента VERIFIED_AUTHOR."""
    async with ASGITransport(app=test_app) as transport:
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            user_data = {
                "name": "Test Author",
                "email": f"{uuid.uuid4()}@test.com",
                "password": "password123",
            }
            register_response = await c.post("/api/v1/auth/register", json=user_data)
            assert register_response.status_code == 201, register_response.text
            user_id = register_response.json()["id"]

            async with async_session_maker() as session:
                result = await session.execute(select(User).where(User.id == user_id))
                user_to_update = result.scalar_one()
                user_to_update.role = UserRole.VERIFIED_AUTHOR
                await session.commit()

            login_response = await c.post(
                "/api/v1/auth/login",
                data={
                    "username": user_data["email"],
                    "password": user_data["password"],
                },
            )
            tokens = login_response.json()
            c.headers["Authorization"] = f"Bearer {tokens['access_token']}"
            c.user_data = register_response.json()
            c.refresh_token = tokens["refresh_token"]
            yield c


@pytest_asyncio.fixture(scope="function")
async def admin_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Фикстура для авторизованного клиента ADMIN."""
    async with ASGITransport(app=test_app) as transport:
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            user_data = {
                "name": "Test Admin",
                "email": f"{uuid.uuid4()}@test.com",
                "password": "password123",
            }
            register_response = await c.post("/api/v1/auth/register", json=user_data)
            assert register_response.status_code == 201, register_response.text
            user_id = register_response.json()["id"]

            async with async_session_maker() as session:
                result = await session.execute(select(User).where(User.id == user_id))
                user_to_update = result.scalar_one()
                user_to_update.role = UserRole.ADMIN
                await session.commit()

            login_response = await c.post(
                "/api/v1/auth/login",
                data={
                    "username": user_data["email"],
                    "password": user_data["password"],
                },
            )
            tokens = login_response.json()
            c.headers["Authorization"] = f"Bearer {tokens['access_token']}"
            c.user_data = register_response.json()
            c.refresh_token = tokens["refresh_token"]
            yield c
