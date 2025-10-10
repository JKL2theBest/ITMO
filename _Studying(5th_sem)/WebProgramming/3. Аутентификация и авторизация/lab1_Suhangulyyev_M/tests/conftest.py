import asyncio
from typing import AsyncGenerator, Callable, Tuple
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool
from sqlalchemy.engine import create_engine as create_sync_engine

import os
from alembic import command
from alembic.config import Config
from app.core.config import settings
from app.db.session import get_db_session
from app.main import app
from app.models.user import User
from app.schemas.role import UserRole

# --- НАСТРОЙКА ТЕСТОВОЙ БД ---
TEST_DATABASE_URL_ASYNC = settings.TEST_DATABASE_URL
TEST_DATABASE_URL_SYNC = settings.SYNC_TEST_DATABASE_URL

engine_test_async = create_async_engine(TEST_DATABASE_URL_ASYNC, poolclass=NullPool)
async_session_maker = async_sessionmaker(
    engine_test_async, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="function")
def db_session_test() -> async_sessionmaker[AsyncSession]:
    """Фикстура, предоставляющая sessionmaker для тестовой БД."""
    return async_session_maker


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    os.environ["TESTING"] = "1"

    db_name = TEST_DATABASE_URL_SYNC.split("/")[-1]
    db_url_for_creation = TEST_DATABASE_URL_SYNC.replace(f"/{db_name}", "/postgres")

    sync_engine = create_sync_engine(db_url_for_creation, isolation_level="AUTOCOMMIT")
    with sync_engine.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {db_name} WITH (FORCE)"))
        conn.execute(text(f"CREATE DATABASE {db_name}"))
    sync_engine.dispose()

    config = Config("alembic.ini")
    command.upgrade(config, "head")

    yield

    sync_engine = create_sync_engine(db_url_for_creation, isolation_level="AUTOCOMMIT")
    with sync_engine.connect() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {db_name} WITH (FORCE)"))
    sync_engine.dispose()
    del os.environ["TESTING"]


@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_maker() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_async_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def authenticated_client_factory() -> AsyncGenerator[Callable, None]:
    clients = []

    async def _create_client(
        role: UserRole,
        email: str | None = None,
        password: str | None = None,
    ) -> Tuple[AsyncClient, dict]:
        async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
            async with async_session_maker() as session:
                yield session

        app.dependency_overrides[get_db_session] = override_get_async_session
        transport = ASGITransport(app=app)
        auth_client = AsyncClient(transport=transport, base_url="http://test")
        clients.append(auth_client)

        email = email or f"{uuid4()}@test.com"
        password = password or "password123"
        user_data = {"name": f"{role.value}_user", "email": email, "password": password}

        register_response = await auth_client.post(
            "/api/v1/auth/register", json=user_data
        )
        assert register_response.status_code == 201, "Failed to register test user"

        registered_user_data = register_response.json()

        if role != UserRole.USER:
            async with async_session_maker() as session:
                result = await session.execute(select(User).where(User.email == email))
                user_to_update = result.scalar_one_or_none()
                assert (
                    user_to_update is not None
                ), "Test user not found in DB after registration"
                user_to_update.role = role
                await session.commit()

        login_data = {"username": email, "password": password}
        response = await auth_client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200, "Failed to login test user"
        tokens = response.json()
        access_token = tokens["access_token"]

        auth_client.headers["Authorization"] = f"Bearer {access_token}"
        return auth_client, registered_user_data

    yield _create_client

    for c in clients:
        await c.aclose()
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def user_client(authenticated_client_factory: Callable):
    client, _ = await authenticated_client_factory(UserRole.USER)
    return client


@pytest_asyncio.fixture(scope="function")
async def author_client(authenticated_client_factory: Callable):
    client, _ = await authenticated_client_factory(UserRole.VERIFIED_AUTHOR)
    return client


@pytest_asyncio.fixture(scope="function")
async def admin_client(authenticated_client_factory: Callable):
    client, _ = await authenticated_client_factory(UserRole.ADMIN)
    return client


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
