"""
Интеграционные тесты для AuthService.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import AsyncSessionFactory, engine
from db.models import Base
from schemas.user_schemas import UserCreate
from services.auth_service import AuthService

# Используем асинхронный маркер для всего файла
pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(scope="module", autouse=True)
async def setup_test_database():
    """
    Создает и очищает тестовую базу данных один раз для всех тестов в модуле.
    """
    # Убедимся, что мы работаем с тестовой БД в памяти
    assert "sqlite" in str(engine.url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """
    Предоставляет чистую сессию с транзакцией для каждого теста.
    Явно откатывает транзакцию после завершения теста.
    """
    async with AsyncSessionFactory() as session:
        # Транзакцию начинаем вручную
        transaction = await session.begin()
        try:
            yield session
        finally:
            # После теста всегда откатываем изменения
            await transaction.rollback()


@pytest_asyncio.fixture
async def auth_service(db_session: AsyncSession) -> AuthService:
    """Фикстура для создания экземпляра AuthService."""
    return AuthService(db_session)


async def test_register_user_success(auth_service: AuthService):
    """
    Тест успешной регистрации нового пользователя.
    """
    user_data = UserCreate(username="testuser", password="StrongPassword123!")

    new_user = await auth_service.register_user(user_data)

    assert new_user is not None
    assert new_user.username == "testuser"
    assert new_user.role_name == "user"


async def test_register_user_duplicate_username(auth_service: AuthService):
    """
    Тест ошибки регистрации с уже существующим именем пользователя.
    """
    user_data = UserCreate(username="duplicate_user", password="Password1")
    await auth_service.register_user(user_data)  # Сначала регистрируем

    # Пытаемся зарегистрировать снова и ожидаем ошибку
    with pytest.raises(ValueError, match="is already taken"):
        await auth_service.register_user(user_data)


async def test_authenticate_user_success(auth_service: AuthService):
    """
    Тест успешной аутентификации.
    """
    password = "MySecurePassword_123"
    user_data = UserCreate(username="auth_user", password=password)
    await auth_service.register_user(user_data)

    # Пробуем аутентифицироваться
    session_token = await auth_service.authenticate_user(user_data.username, password)

    assert session_token is not None
    assert isinstance(session_token, str)


async def test_authenticate_user_wrong_password(auth_service: AuthService):
    """
    Тест ошибки аутентификации с неверным паролем.
    """
    user_data = UserCreate(username="wrong_pass_user", password="CorrectPassword1")
    await auth_service.register_user(user_data)

    with pytest.raises(ValueError, match="Invalid username or password"):
        await auth_service.authenticate_user(user_data.username, "WrongPassword1")


async def test_authenticate_user_nonexistent_user(auth_service: AuthService):
    """
    Тест ошибки аутентификации для несуществующего пользователя.
    """
    with pytest.raises(ValueError, match="Invalid username or password"):
        await auth_service.authenticate_user("ghost_user", "any_password")
