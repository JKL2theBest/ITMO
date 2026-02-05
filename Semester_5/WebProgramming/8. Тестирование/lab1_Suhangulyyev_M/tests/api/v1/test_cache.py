import pytest
from httpx import AsyncClient
from redis.asyncio import Redis as AsyncRedis
from app.repositories.sqlalchemy.news import NewsRepository
from app.repositories.sqlalchemy.user import UserRepository

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def news_item_for_cache(author_client: AsyncClient) -> dict:
    """Создает новость и возвращает её данные."""
    response = await author_client.post(
        "/api/v1/news/",
        json={"title": "Cache Test News", "content": {"body": "test"}},
    )
    assert response.status_code == 201
    return response.json()


async def test_news_get_is_cached(
    user_client: AsyncClient,
    news_item_for_cache: dict,
    mocker,
):
    """Тест: проверка кэширования новости."""
    news_id = news_item_for_cache["id"]
    spy = mocker.spy(NewsRepository, "get_by_id")

    # 1. Первый запрос (должен пойти в БД, spy зафиксирует вызов)
    response1 = await user_client.get(f"/api/v1/news/{news_id}")
    assert response1.status_code == 200
    spy.assert_called_once()

    # 2. Второй запрос (должен быть взят из кэша, spy больше не вызывается)
    response2 = await user_client.get(f"/api/v1/news/{news_id}")
    assert response2.status_code == 200
    spy.assert_called_once()


async def test_news_cache_invalidated_on_update(
    author_client: AsyncClient, news_item_for_cache: dict, test_redis: AsyncRedis
):
    """Тест: кэш новости инвалидируется после ее обновления."""
    news_id = news_item_for_cache["id"]
    cache_key = f"news:{news_id}"

    # "Греем" кэш
    await author_client.get(f"/api/v1/news/{news_id}")
    assert await test_redis.exists(cache_key)

    # Обновляем новость
    await author_client.patch(
        f"/api/v1/news/{news_id}", json={"title": "Updated Title"}
    )

    # Кэш должен исчезнуть
    assert not await test_redis.exists(cache_key)


async def test_user_get_is_cached(
    admin_client: AsyncClient,
    user_client: AsyncClient,
    mocker,
):
    """Тест: запрос к пользователю кэшируется."""
    target_user_id = user_client.user_data["id"]
    spy = mocker.spy(UserRepository, "get_by_id")

    # Первый запрос - "прогрев" кэша.
    await admin_client.get(f"/api/v1/users/{target_user_id}")
    spy.reset_mock()

    # Второй запрос - должен быть из кэша
    await admin_client.get(f"/api/v1/users/{target_user_id}")

    spy.assert_not_called()
