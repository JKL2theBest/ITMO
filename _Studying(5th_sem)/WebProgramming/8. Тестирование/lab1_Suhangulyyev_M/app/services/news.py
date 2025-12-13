import uuid
from redis.asyncio import Redis

from fastapi import HTTPException, status
from app.models.news import News
from app.models.user import User
from app.repositories.sqlalchemy.news import NewsRepository
from app.schemas.news import NewsCreate, NewsCreateIn, NewsUpdate, NewsResponse
from app.services.base import BaseService
from app.worker.tasks import send_new_news_notification
from app.core.metrics import NEWS_CREATED_TOTAL
import structlog

logger = structlog.get_logger()


class NewsService(BaseService):
    _cache_ttl = 300  # 5 минут

    def __init__(self, news_repo: NewsRepository, redis_client: Redis):
        super().__init__(news_repo, redis_client)

    async def get_by_id(self, news_id: uuid.UUID) -> News | None:
        """Получение новости по ID с кэшированием."""
        cache_key = f"news:{news_id}"
        if cached_news := await self.redis.get(cache_key):
            logger.info("News found in cache", news_id=str(news_id))  # JSON log style
            news_schema = NewsResponse.model_validate_json(cached_news)
            return news_schema

        logger.info("News not in cache, fetching from DB", news_id=str(news_id))
        db_news = await self.repository.get_by_id(news_id)

        if not db_news:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"News with id {news_id} not found",
            )

        news_to_cache = NewsResponse.model_validate(db_news)
        await self.redis.set(
            cache_key, news_to_cache.model_dump_json(), ex=self._cache_ttl
        )
        return db_news

    async def create_news(self, news_data: NewsCreateIn, author: User) -> News:
        news_dict = news_data.model_dump()
        news_dict["author_id"] = author.id
        final_news_data = NewsCreate(**news_dict)

        new_news = await self.repository.create(final_news_data)

        # Вызов фоновой задачи
        send_new_news_notification.delay(str(new_news.id))
        logger.info("Task sent for new news notification", news_id=str(new_news.id))

        NEWS_CREATED_TOTAL.inc()

        return new_news

    async def update_news(self, news_to_update: News, news_data: NewsUpdate) -> News:
        """Обновление новости с инвалидацией кэша."""
        updated_news = await self.repository.update(
            db_obj=news_to_update, update_data=news_data
        )
        await self.redis.delete(f"news:{updated_news.id}")
        logger.info("Cache invalidated", news_id=str(updated_news.id))
        return updated_news

    async def delete_news(self, news_to_delete: News) -> None:
        """Удаление новости с инвалидацией кэша."""
        news_id = news_to_delete.id
        await self.repository.delete(db_obj=news_to_delete)
        await self.redis.delete(f"news:{news_id}")
        logger.info("Cache invalidated", news_id=str(news_id))
