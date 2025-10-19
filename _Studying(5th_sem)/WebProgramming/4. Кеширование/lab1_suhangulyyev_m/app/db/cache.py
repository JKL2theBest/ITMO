from typing import AsyncGenerator
import redis.asyncio as aioredis
from app.core.config import settings

redis_pool = None


async def init_redis_pool():
    global redis_pool
    redis_pool = aioredis.ConnectionPool.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
        decode_responses=True,
    )


async def get_redis_client() -> AsyncGenerator[aioredis.Redis, None]:
    if not redis_pool:
        raise ConnectionError("Redis connection pool is not initialized")
    async with aioredis.Redis(connection_pool=redis_pool) as client:
        yield client


async def close_redis_pool():
    if redis_pool:
        await redis_pool.disconnect()
