import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
import pytest
import app.db.cache as cache_module


def run_async(coro):
    return asyncio.run(coro)


def test_init_and_close_redis_pool():
    """
    Тест проверяет:
    1. Инициализацию пула (init_redis_pool).
    2. Закрытие пула (close_redis_pool).
    """

    async def _test():
        cache_module.redis_pool = None

        mock_pool = MagicMock()
        mock_pool.disconnect = AsyncMock()

        with patch(
            "app.db.cache.aioredis.ConnectionPool.from_url", return_value=mock_pool
        ) as mock_from_url:
            # 1. Инициализация
            await cache_module.init_redis_pool()

            assert cache_module.redis_pool is not None
            assert cache_module.redis_pool == mock_pool
            mock_from_url.assert_called_once()

            await cache_module.init_redis_pool()
            mock_from_url.assert_called_once()

            # 2. Закрытие
            await cache_module.close_redis_pool()

            mock_pool.disconnect.assert_awaited_once()
            assert cache_module.redis_pool is None

            await cache_module.close_redis_pool()

    run_async(_test())


def test_get_redis_client_flow():
    """
    Тест проверяет работу генератора get_redis_client.
    """

    async def _test():
        cache_module.redis_pool = None

        mock_pool_instance = MagicMock()
        mock_pool_instance.disconnect = AsyncMock(return_value=None)

        mock_redis_instance = AsyncMock()

        mock_context_manager = MagicMock()
        mock_context_manager.__aenter__ = AsyncMock(return_value=mock_redis_instance)
        mock_context_manager.__aexit__ = AsyncMock(return_value=None)

        mock_redis_cls = MagicMock(return_value=mock_context_manager)

        with patch(
            "app.db.cache.aioredis.ConnectionPool.from_url",
            return_value=mock_pool_instance,
        ), patch("app.db.cache.aioredis.Redis", new=mock_redis_cls):

            gen = cache_module.get_redis_client()

            client = await gen.__anext__()

            assert cache_module.redis_pool is not None
            assert client == mock_redis_instance

            try:
                await gen.__anext__()
            except StopAsyncIteration:
                pass

            mock_context_manager.__aexit__.assert_awaited_once()

        await cache_module.close_redis_pool()
        mock_pool_instance.disconnect.assert_awaited_once()

    run_async(_test())


def test_get_redis_client_connection_error():
    """
    Тест проверяет выброс ConnectionError, если пул не создался.
    """

    async def _test():
        cache_module.redis_pool = None

        with patch("app.db.cache.init_redis_pool") as mock_init:

            gen = cache_module.get_redis_client()

            with pytest.raises(ConnectionError) as exc:
                await gen.__anext__()

            assert "Redis connection pool could not be initialized" in str(exc.value)
            mock_init.assert_awaited_once()

    run_async(_test())
