import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from jose import jwt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
import uuid
from typing import AsyncGenerator

from app.api.dependencies import get_db_session
from app.core.config import settings
from app.db.models import Base
from app.main import app

# --- Настройка тестовой среды ---
TEST_DATABASE_URL = str(settings.DATABASE_URL) + "_test"

# --- Фикстуры ---


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """
    Создает и удаляет тестовую базу данных один раз за сессию.
    """
    db_name = TEST_DATABASE_URL.split("/")[-1]
    tmp_engine = create_async_engine(
        TEST_DATABASE_URL.replace(f"/{db_name}", "/postgres"),
        isolation_level="AUTOCOMMIT",
    )
    async with tmp_engine.connect() as conn:
        res = await conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname='{db_name}'")
        )
        if not res.scalar():
            await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    await tmp_engine.dispose()

    # Создаем таблицы в тестовой БД
    test_engine = create_async_engine(TEST_DATABASE_URL)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # Тесты выполняются здесь

    # --- Очистка ---
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()

    async with tmp_engine.connect() as conn:
        await conn.execute(
            text(
                f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{db_name}'"
            )
        )
        await conn.execute(text(f'DROP DATABASE "{db_name}"'))
    await tmp_engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def async_client() -> AsyncClient:
    """
    Создаёт HTTP-клиент с тестовой БД и подменённой зависимостью get_db_session.
    """
    test_engine = create_async_engine(TEST_DATABASE_URL)

    TestAsyncSessionLocal = async_sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )

    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        async with TestAsyncSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    del app.dependency_overrides[get_db_session]

    await test_engine.dispose()


# --- Тесты ---


@pytest.mark.asyncio(scope="session")
class TestAuth:
    """Набор тестов для проверки регистрации и аутентификации."""

    def short_uuid(self):
        """Генерирует короткий уникальный суффикс для логинов."""
        return str(uuid.uuid4())[:8]

    # Каждый тест теперь получает один и тот же `async_client` на всю сессию,
    # но override для `get_db_session` гарантирует, что каждый запрос
    # получит свежую, чистую сессию.

    async def test_successful_registration(self, async_client: AsyncClient):
        login = f"user_{self.short_uuid()}"
        response = await async_client.post(
            "/api/v1/auth/register",
            json={"login": login, "password": "TestPassword123!"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["login"] == login

    async def test_duplicate_login_registration(self, async_client: AsyncClient):
        login = f"dup_{self.short_uuid()}"
        response1 = await async_client.post(
            "/api/v1/auth/register",
            json={"login": login, "password": "TestPassword123!"},
        )
        assert response1.status_code == 201
        response2 = await async_client.post(
            "/api/v1/auth/register",
            json={"login": login, "password": "AnotherPassword123!"},
        )
        assert response2.status_code == 409

    @pytest.mark.parametrize(
        "login, password",
        [
            ("u1", "TestPassword123!"),
            ("user-test!", "TestPassword123!"),
            (f"long_login_{'a'*30}", "TestPassword123!"),
            ("testuser_val", "short"),
            ("testuser_val", "nouppercase1!"),
            ("testuser_val", "NOLOWERCASE1!"),
            ("testuser_val", "NoDigit!"),
            ("testuser_val", "NoSpecial1"),
        ],
    )
    async def test_invalid_registration_data(
        self, async_client: AsyncClient, login, password
    ):
        """Проверяет отклонение некорректных логинов и паролей."""
        response = await async_client.post(
            "/api/v1/auth/register", json={"login": login, "password": password}
        )
        assert response.status_code == 422

    async def test_successful_login(self, async_client: AsyncClient):
        """Регистрация и вход с проверкой JWT."""
        login = f"login_{self.short_uuid()}"
        reg_response = await async_client.post(
            "/api/v1/auth/register",
            json={"login": login, "password": "TestPassword123!"},
        )
        assert reg_response.status_code == 201
        user_id = reg_response.json()["id"]

        login_response = await async_client.post(
            "/api/v1/auth/login", json={"login": login, "password": "TestPassword123!"}
        )
        assert login_response.status_code == 200
        data = login_response.json()
        assert "access_token" in data

        token = data["access_token"]
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == login
        assert payload["user_id"] == user_id

    @pytest.mark.parametrize(
        "login_suffix, password",
        [("non_existent", "any_password"), ("wrong_pass", "wrong_password")],
    )
    async def test_failed_login(
        self, async_client: AsyncClient, login_suffix, password
    ):
        """Проверяет ошибку авторизации при неверных данных."""
        login = f"{login_suffix}_{self.short_uuid()}"
        if login_suffix == "wrong_pass":
            await async_client.post(
                "/api/v1/auth/register",
                json={"login": login, "password": "TestPassword123!"},
            )
        response = await async_client.post(
            "/api/v1/auth/login", json={"login": login, "password": password}
        )
        assert response.status_code == 401
