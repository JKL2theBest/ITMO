import uuid
import asyncio
import datetime
from unittest.mock import AsyncMock, MagicMock, ANY
from app.worker.tasks import _send_notification_async, _send_digest_async
from fakeredis.aioredis import FakeRedis


def run_async(coro):
    return asyncio.run(coro)


def test_send_notification_success(mocker):
    """
    Тест: успешная отправка уведомления о новости.
    """

    async def _test():
        redis = FakeRedis(decode_responses=True)
        news_id = str(uuid.uuid4())

        mocker.patch("app.worker.tasks.aioredis.from_url", return_value=redis)
        mock_logger = mocker.patch("app.worker.tasks.logger")

        mock_engine = AsyncMock()
        mock_engine.dispose.return_value = None
        mocker.patch("app.worker.tasks.create_async_engine", return_value=mock_engine)

        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mocker.patch(
            "app.worker.tasks.async_sessionmaker", return_value=lambda: mock_session
        )

        mock_news_result = MagicMock()
        mock_news = MagicMock()
        mock_news.title = "Test News"
        mock_news_result.scalar_one_or_none.return_value = mock_news

        mock_users_result = MagicMock()
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_users_result.scalars.return_value.all.return_value = [mock_user]

        mock_session.execute.side_effect = [mock_news_result, mock_users_result]

        # Запуск
        await _send_notification_async(news_id)

        # Проверки
        assert await redis.exists(f"news-notification-sent:{news_id}")

        mock_logger.info.assert_any_call(
            "SEND_EMAIL", recipient="test@example.com", subject="New Article!", body=ANY
        )
        await redis.aclose()

    run_async(_test())


def test_send_notification_idempotency(mocker):
    """
    Тест: повторный запуск задачи не должен отправлять письма.
    """

    async def _test():
        redis = FakeRedis(decode_responses=True)
        news_id = str(uuid.uuid4())

        await redis.set(f"news-notification-sent:{news_id}", "1")

        mocker.patch("app.worker.tasks.aioredis.from_url", return_value=redis)
        mock_logger = mocker.patch("app.worker.tasks.logger")

        mock_engine = AsyncMock()
        mock_engine.dispose.return_value = None
        mocker.patch("app.worker.tasks.create_async_engine", return_value=mock_engine)

        await _send_notification_async(news_id)

        mock_logger.warning.assert_called_with(
            "Notification already sent. Skipping.", news_id=news_id
        )
        mock_logger.info.assert_not_called()
        await redis.aclose()

    run_async(_test())


def test_send_notification_news_not_found(mocker):
    """
    Тест: обработка ситуации, когда новость не найдена в БД.
    """

    async def _test():
        redis = FakeRedis(decode_responses=True)
        news_id = str(uuid.uuid4())

        mocker.patch("app.worker.tasks.aioredis.from_url", return_value=redis)
        mock_logger = mocker.patch("app.worker.tasks.logger")

        mock_engine = AsyncMock()
        mock_engine.dispose.return_value = None
        mocker.patch("app.worker.tasks.create_async_engine", return_value=mock_engine)

        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mocker.patch(
            "app.worker.tasks.async_sessionmaker", return_value=lambda: mock_session
        )

        # Результат - MagicMock (синхронный)
        mock_news_result = MagicMock()
        mock_news_result.scalar_one_or_none.return_value = None

        mock_users_result = MagicMock()
        mock_users_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_news_result, mock_users_result]

        await _send_notification_async(news_id)

        assert await redis.exists(f"news-notification-sent:{news_id}")
        mock_logger.error.assert_called_with("News not found", news_id=news_id)
        await redis.aclose()

    run_async(_test())


def test_weekly_digest_success(mocker):
    """
    Тест: сборка еженедельного дайджеста.
    """

    async def _test():
        redis = FakeRedis(decode_responses=True)

        mocker.patch("app.worker.tasks.aioredis.from_url", return_value=redis)
        mock_logger = mocker.patch("app.worker.tasks.logger")

        mock_engine = AsyncMock()
        mock_engine.dispose.return_value = None
        mocker.patch("app.worker.tasks.create_async_engine", return_value=mock_engine)

        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mocker.patch(
            "app.worker.tasks.async_sessionmaker", return_value=lambda: mock_session
        )

        # Новости - MagicMock
        mock_news_result = MagicMock()
        mock_news = MagicMock()
        mock_news.title = "Digest News"
        mock_news.author.name = "Author"
        mock_news_result.scalars.return_value.all.return_value = [mock_news]

        # Пользователи - MagicMock
        mock_users_result = MagicMock()
        mock_user = MagicMock()
        mock_user.email = "digest@test.com"
        mock_users_result.scalars.return_value.all.return_value = [mock_user]

        mock_session.execute.side_effect = [mock_news_result, mock_users_result]

        await _send_digest_async()

        keys = await redis.keys("weekly-digest-sent:*")
        assert len(keys) == 1

        mock_logger.info.assert_any_call(
            "SEND_EMAIL_DIGEST",
            recipient="digest@test.com",
            subject="Weekly News Digest",
        )
        await redis.aclose()

    run_async(_test())


def test_weekly_digest_idempotency(mocker):
    """
    Тест: дайджест не отправляется дважды.
    """

    async def _test():
        redis = FakeRedis(decode_responses=True)
        today = datetime.datetime.utcnow().date()
        start_of_week = today - datetime.timedelta(days=today.weekday())
        key = f"weekly-digest-sent:{start_of_week.isoformat()}"

        await redis.set(key, "1")

        mocker.patch("app.worker.tasks.aioredis.from_url", return_value=redis)
        mock_logger = mocker.patch("app.worker.tasks.logger")

        mock_engine = AsyncMock()
        mock_engine.dispose.return_value = None
        mocker.patch("app.worker.tasks.create_async_engine", return_value=mock_engine)

        await _send_digest_async()

        mock_logger.warning.assert_called_with(
            "Weekly digest already sent. Skipping.", week=str(start_of_week)
        )
        await redis.aclose()

    run_async(_test())
