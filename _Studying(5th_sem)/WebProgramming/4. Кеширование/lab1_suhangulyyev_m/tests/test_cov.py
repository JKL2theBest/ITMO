import pytest
from unittest.mock import AsyncMock, MagicMock
import redis.asyncio as aioredis

from app.main import app, lifespan
import app.db.cache as cache_module

pytestmark = pytest.mark.asyncio


async def test_lifespan_redis_connection(mocker):
    """
    Тест: проверяет, что lifespan-контекст корректно создает и закрывает пул Redis.
    """
    mock_pool = MagicMock()
    mock_pool.disconnect = AsyncMock()
    mocker.patch.object(aioredis.ConnectionPool, "from_url", return_value=mock_pool)

    async with lifespan(app):
        assert cache_module.redis_pool is not None
        assert cache_module.redis_pool == mock_pool

    mock_pool.disconnect.assert_called_once()


async def test_get_redis_client_not_initialized():
    """
    Тест: проверяет, что если пул соединений не инициализирован,
    выбрасывается исключение ConnectionError.
    """
    original_pool = cache_module.redis_pool
    cache_module.redis_pool = None

    with pytest.raises(
        ConnectionError, match="Redis connection pool is not initialized"
    ):
        async for _ in cache_module.get_redis_client():
            pass  # Этот код не должен выполниться

    cache_module.redis_pool = original_pool
