import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock

pytestmark = pytest.mark.asyncio


async def test_create_news_sends_notification(author_client: AsyncClient, mocker):
    """
    Тест: проверяет, что при создании новости вызывается фоновая задача.
    """
    mock_task = mocker.patch("app.services.news.send_new_news_notification")
    mock_task.delay = MagicMock()

    response = await author_client.post(
        "/api/v1/news/",
        json={"title": "Test Celery Task", "content": {"body": "test"}},
    )

    assert response.status_code == 201
    news_id = response.json()["id"]

    mock_task.delay.assert_called_once_with(str(news_id))
