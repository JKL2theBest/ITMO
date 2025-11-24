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


async def test_get_redis_client_lazy_initialization():
    """
    Тест: проверяет, что если пул соединений не инициализирован,
    он будет создан при первом вызове get_redis_client.
    """
    original_pool = cache_module.redis_pool
    cache_module.redis_pool = None

    assert cache_module.redis_pool is None

    async for client in cache_module.get_redis_client():
        assert client is not None
        assert isinstance(client, aioredis.Redis)

    assert cache_module.redis_pool is not None

    await cache_module.close_redis_pool()
    cache_module.redis_pool = original_pool
