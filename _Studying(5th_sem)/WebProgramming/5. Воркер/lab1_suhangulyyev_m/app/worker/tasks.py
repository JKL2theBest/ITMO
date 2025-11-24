import asyncio
import uuid
from datetime import datetime, timedelta

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.core.config import settings

from app.models import User, News
from app.worker.celery_app import celery_app, celery_logger

logger = celery_logger


@celery_app.task(
    bind=True,
    autoretry_for=(ConnectionError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def send_new_news_notification(self, news_id: str):
    """
    Синхронная задача-обертка, которая запускает асинхронную логику.
    """
    asyncio.run(_send_notification_async(news_id))


async def _send_notification_async(news_id: str):
    """
    Асинхронная логика для отправки уведомлений.
    """
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    local_session_maker = async_sessionmaker(engine, expire_on_commit=False)

    redis = aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0", decode_responses=True
    )

    try:
        idempotency_key = f"news-notification-sent:{news_id}"
        if not await redis.set(idempotency_key, "1", ex=3600, nx=True):
            logger.warning(
                f"Notification for news_id {news_id} already sent. Skipping."
            )
            return

        async with local_session_maker() as session:
            news_result = await session.execute(
                select(News).filter_by(id=uuid.UUID(news_id))
            )
            news = news_result.scalar_one_or_none()

            users_result = await session.execute(select(User))
            users = users_result.scalars().all()

            if not news:
                logger.error(f"News with id {news_id} not found.")
                return

            for user in users:
                log_message = (
                    f"SEND_EMAIL: To: {user.email} | Subject: New Article! | "
                    f"Body: '{news.title}' has been published."
                )
                logger.info(log_message)
    finally:
        await redis.close()
        await engine.dispose()


@celery_app.task(
    bind=True,
    autoretry_for=(ConnectionError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_weekly_digest(self):
    """Синхронная задача-обертка для еженедельного дайджеста."""
    asyncio.run(_send_digest_async())


async def _send_digest_async():
    """Асинхронная логика для отправки дайджеста."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    local_session_maker = async_sessionmaker(engine, expire_on_commit=False)

    redis = aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0", decode_responses=True
    )

    try:
        today = datetime.utcnow().date()
        start_of_week = today - timedelta(days=today.weekday())
        idempotency_key = f"weekly-digest-sent:{start_of_week.isoformat()}"

        if not await redis.set(
            idempotency_key, "1", ex=timedelta(days=8).total_seconds(), nx=True
        ):
            logger.warning(
                f"Weekly digest for week of {start_of_week} already sent. Skipping."
            )
            return

        async with local_session_maker() as session:
            one_week_ago = datetime.utcnow() - timedelta(days=7)

            news_result = await session.execute(
                select(News)
                .filter(News.published_at >= one_week_ago)
                .options(selectinload(News.author))
                .order_by(News.published_at.desc())
            )
            recent_news = news_result.scalars().all()

            users_result = await session.execute(select(User))
            users = users_result.scalars().all()

            if not recent_news:
                logger.info("No new news this week. Skipping digest.")
                return

            news_titles = "\n - ".join(
                [f'"{news.title}" by {news.author.name}' for news in recent_news]
            )
            email_body = f"Here are the latest news from this week:\n - {news_titles}"

            for user in users:
                log_message = f"SEND_EMAIL_DIGEST: To: {user.email} | Subject: Weekly News Digest | Body: {email_body}"
                logger.info(log_message)
    finally:
        await redis.close()
        await engine.dispose()
