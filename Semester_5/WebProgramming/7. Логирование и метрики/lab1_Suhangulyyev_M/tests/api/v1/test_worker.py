import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock

pytestmark = pytest.mark.asyncio


async def test_create_news_sends_notification(author_client: AsyncClient, mocker):
    """
    Тест: проверяет, что при создании новости вызывается фоновая задача
    send_new_news_notification.delay() с правильным ID.
    """
    mock_send_notification: MagicMock = mocker.patch(
        "app.worker.tasks.send_new_news_notification.delay"
    )

    response = await author_client.post(
        "/api/v1/news/",
        json={"title": "Test Celery Task", "content": {"body": "test"}},
    )

    assert response.status_code == 201
    news_id = response.json()["id"]

    # Главная проверка: убеждаемся, что наш "мок" .delay() был вызван ровно 1 раз
    mock_send_notification.assert_called_once()
    # И что он был вызван с правильным аргументом - ID созданной новости
    mock_send_notification.assert_called_with(news_id)
