# ruff: noqa: E402
import os
import shutil
import tempfile
import asyncio
import uuid
from typing import AsyncGenerator
import datetime

# Нужен для разрешения конфликтов вложенных циклов
import nest_asyncio

nest_asyncio.apply()

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
from fakeredis.aioredis import FakeRedis

from alembic import command
from alembic.config import Config

from app.core.config import settings
from app.db.cache import get_redis_client
from app.db.session import get_db_session
from app.main import app
from app.models.user import User
from app.schemas.role import UserRole
from app.core.security import hash_password


# --- Явное определение Event Loop ---
@pytest.fixture(scope="function")
def event_loop():
    """
    Создает fresh event loop для каждого теста.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


# --- Настройка БД ---
engine_test = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
async_session_maker = async_sessionmaker(
    engine_test, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """
    Применяет миграции и чистит данные.
    """
    # 1. Миграции
    config = Config("alembic.ini")
    command.upgrade(config, "head")

    # 2. Очистка
    sync_engine = create_sync_engine(settings.SYNC_DATABASE_URL)
    with sync_engine.connect() as conn:
        conn.execute(text("COMMIT"))
        conn.execute(
            text("TRUNCATE TABLE users, news, comments RESTART IDENTITY CASCADE;")
        )
        conn.commit()

        # 3. Восстановление Админа
        # Критично для E2E тестов, которые ожидают наличие админа
        admin_id = uuid.uuid4()
        conn.execute(
            text(
                """
            INSERT INTO users (id, name, email, hashed_password, role, registered_at)
            VALUES (:id, :name, :email, :password, :role, :reg_at)
            """
            ),
            {
                "id": admin_id,
                "name": "Admin User",
                "email": "admin@example.com",
                "password": hash_password("admin_password"),
                "role": "ADMIN",
                "reg_at": datetime.datetime.now(datetime.timezone.utc),
            },
        )
        conn.commit()

    yield

    sync_engine.dispose()
    if os.path.exists(TEST_METRICS_DIR):
        shutil.rmtree(TEST_METRICS_DIR, ignore_errors=True)


# --- Redis ---
@pytest_asyncio.fixture(scope="function")
async def test_redis() -> AsyncGenerator[FakeRedis, None]:
    """Фикстура, создающая фейковый клиент Redis для тестов."""
    client = FakeRedis(decode_responses=True)
    await client.flushall()
    yield client
    await client.flushall()
    await client.aclose()


# --- App ---
@pytest_asyncio.fixture(scope="function")
async def test_app(test_redis: FakeRedis) -> AsyncGenerator[FastAPI, None]:
    """Фикстура для создания экземпляра тестового приложения с переопределенными зависимостями."""

    async def override_get_db_session():
        async with async_session_maker() as session:
            yield session

    async def override_get_redis_client():
        yield test_redis

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_redis_client] = override_get_redis_client

    app.router.lifespan_context = None
    yield app

    app.dependency_overrides.clear()


# --- Клиенты ---
@pytest_asyncio.fixture(scope="function")
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Фикстура для неавторизованного HTTP клиента."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _setup_auth_client(app_instance: FastAPI, role: UserRole) -> AsyncClient:
    """
    Вспомогательная фабрика для создания авторизованного клиента с определенной ролью.
    """
    transport = ASGITransport(app=app_instance)
    client = AsyncClient(transport=transport, base_url="http://test")

    user_data = {
        "name": f"Test {role.value.capitalize()}",
        "email": f"{uuid.uuid4()}@test.com",
        "password": "password123",
    }

    reg_res = await client.post("/api/v1/auth/register", json=user_data)
    if reg_res.status_code != 201:
        await client.aclose()
        raise RuntimeError(f"Register failed: {reg_res.text}")

    user_id = reg_res.json()["id"]

    if role != UserRole.USER:
        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.id == uuid.UUID(user_id))
            )
            user_to_update = result.scalar_one()
            user_to_update.role = role
            await session.commit()
            async for redis_client in app_instance.dependency_overrides[
                get_redis_client
            ]():
                await redis_client.delete(f"user:{user_id}")

    login_res = await client.post(
        "/api/v1/auth/login",
        data={"username": user_data["email"], "password": user_data["password"]},
    )
    if login_res.status_code != 200:
        await client.aclose()
        raise RuntimeError(f"Login failed: {login_res.text}")

    tokens = login_res.json()
    client.headers["Authorization"] = f"Bearer {tokens['access_token']}"
    client.user_data = reg_res.json()
    client.refresh_token = tokens["refresh_token"]

    return client


@pytest_asyncio.fixture(scope="function")
async def user_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Фикстура для авторизованного клиента USER."""
    client = await _setup_auth_client(test_app, UserRole.USER)
    yield client
    await client.aclose()


@pytest_asyncio.fixture(scope="function")
async def author_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Фикстура для авторизованного клиента VERIFIED_AUTHOR."""
    client = await _setup_auth_client(test_app, UserRole.VERIFIED_AUTHOR)
    yield client
    await client.aclose()


@pytest_asyncio.fixture(scope="function")
async def admin_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Фикстура для авторизованного клиента ADMIN."""
    client = await _setup_auth_client(test_app, UserRole.ADMIN)
    yield client
    await client.aclose()
