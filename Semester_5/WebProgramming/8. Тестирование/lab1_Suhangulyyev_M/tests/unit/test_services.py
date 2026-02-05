import pytest
import uuid
import asyncio
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from fakeredis.aioredis import FakeRedis

from app.services.users import UserService
from app.services.news import NewsService
from app.schemas.user import UserCreate
from app.schemas.news import NewsResponse
from app.models.user import User
from app.schemas.role import UserRole


# Вспомогательная функция для запуска асинхронного кода
def run_async(coro):
    return asyncio.run(coro)


def test_create_user_success():
    """Unit: Успешное создание пользователя."""

    async def _test():
        # Локальный Redis, чтобы не зависеть от глобальных фикстур
        redis = FakeRedis(decode_responses=True)

        mock_repo = AsyncMock()
        mock_repo.get_by_email.return_value = None
        mock_repo.model = User
        mock_repo.session.add = MagicMock()
        mock_repo.session.commit = AsyncMock()
        mock_repo.session.refresh = AsyncMock()

        service = UserService(user_repo=mock_repo, redis_client=redis)
        user_in = UserCreate(name="Test", email="test@test.com", password="pass")

        result = await service.create_user(user_in)

        mock_repo.get_by_email.assert_called_once_with("test@test.com")
        mock_repo.session.add.assert_called_once()
        mock_repo.session.commit.assert_called_once()
        assert isinstance(result, User)
        await redis.aclose()

    run_async(_test())


def test_create_user_duplicate_email():
    """Unit: Ошибка при дубликате email."""

    async def _test():
        redis = FakeRedis(decode_responses=True)

        mock_repo = AsyncMock()
        mock_repo.get_by_email.return_value = User(
            id=uuid.uuid4(), email="exist@test.com"
        )

        service = UserService(user_repo=mock_repo, redis_client=redis)
        user_in = UserCreate(name="Test", email="exist@test.com", password="pass")

        with pytest.raises(HTTPException) as exc:
            await service.create_user(user_in)

        assert exc.value.status_code == 400
        await redis.aclose()

    run_async(_test())


def test_get_news_cache_hit():
    """Unit: Получение новости из кэша."""

    async def _test():
        redis = FakeRedis(decode_responses=True)

        mock_repo = AsyncMock()
        service = NewsService(news_repo=mock_repo, redis_client=redis)

        news_id = uuid.uuid4()
        author_data = {
            "id": str(uuid.uuid4()),
            "name": "Auth",
            "email": "e@e.com",
            "role": UserRole.USER,
            "registered_at": "2025-01-01T00:00:00Z",
            "avatar_url": None,
        }
        cached_data = NewsResponse(
            id=news_id,
            title="Cached",
            content={},
            published_at="2025-01-01T00:00:00Z",
            author=author_data,
        ).model_dump_json()

        await redis.set(f"news:{news_id}", cached_data)

        result = await service.get_by_id(news_id)
        assert result.title == "Cached"
        mock_repo.get_by_id.assert_not_called()
        await redis.aclose()

    run_async(_test())


def test_get_news_db_miss_and_not_found():
    """Unit: Новость не найдена ни в кэше, ни в БД."""

    async def _test():
        redis = FakeRedis(decode_responses=True)

        mock_repo = AsyncMock()
        mock_repo.get_by_id.return_value = None

        service = NewsService(news_repo=mock_repo, redis_client=redis)
        news_id = uuid.uuid4()

        with pytest.raises(HTTPException) as exc:
            await service.get_by_id(news_id)

        assert exc.value.status_code == 404
        await redis.aclose()

    run_async(_test())
