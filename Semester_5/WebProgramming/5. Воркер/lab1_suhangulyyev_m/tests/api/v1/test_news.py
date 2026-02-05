import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_user_cannot_create_news(user_client: AsyncClient):
    """Тест: обычный пользователь не может создать новость."""
    response = await user_client.post(
        "/api/v1/news/",
        json={"title": "Forbidden Title", "content": {}},
    )
    assert response.status_code == 403


async def test_author_can_create_news(author_client: AsyncClient):
    """Тест: верифицированный автор может создать новость."""
    response = await author_client.post(
        "/api/v1/news/",
        json={"title": "Author's Title", "content": {"body": "text"}},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Author's Title"
    assert data["author"]["role"] == "verified_author"


async def test_get_news_unauthorized(client: AsyncClient):
    """Тест: неавторизованный пользователь не может получить список новостей."""
    response = await client.get("/api/v1/news/")
    assert response.status_code == 401


async def test_get_news_authorized(user_client: AsyncClient):
    """Тест: авторизованный пользователь может получить список новостей."""
    response = await user_client.get("/api/v1/news/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.fixture
async def created_news(author_client: AsyncClient) -> dict:
    """Фикстура для создания новости для тестов обновления/удаления."""
    response = await author_client.post(
        "/api/v1/news/",
        json={"title": "Test News for Ownership", "content": {}},
    )
    assert response.status_code == 201
    return response.json()


async def test_author_can_update_own_news(
    author_client: AsyncClient, created_news: dict
):
    """Тест: автор может обновить свою новость."""
    news_id = created_news["id"]
    response = await author_client.patch(
        f"/api/v1/news/{news_id}", json={"title": "Updated by Author"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated by Author"


async def test_author_can_delete_own_news(author_client: AsyncClient):
    """Тест: автор может удалить свою новость."""
    response = await author_client.post(
        "/api/v1/news/", json={"title": "To Be Deleted", "content": {}}
    )
    news_id = response.json()["id"]

    delete_response = await author_client.delete(f"/api/v1/news/{news_id}")
    assert delete_response.status_code == 204

    get_response = await author_client.get(f"/api/v1/news/{news_id}")
    assert get_response.status_code == 404


async def test_permissions_on_other_news(
    user_client: AsyncClient, author_client: AsyncClient, admin_client: AsyncClient
):
    """Тест: юзер не может менять чужие новости, а админ может."""
    # 1. Автор создает новость
    response = await author_client.post(
        "/api/v1/news/", json={"title": "Ownership Test", "content": {}}
    )
    assert response.status_code == 201
    news_id = response.json()["id"]

    # 2. Обычный юзер пытается ее изменить (неуспешно)
    patch_response_user = await user_client.patch(
        f"/api/v1/news/{news_id}", json={"title": "Hacked Title"}
    )
    assert patch_response_user.status_code == 403

    # 3. Админ пытается ее изменить (успешно)
    admin_patch_response = await admin_client.patch(
        f"/api/v1/news/{news_id}", json={"title": "Admin Updated"}
    )
    assert admin_patch_response.status_code == 200
    assert admin_patch_response.json()["title"] == "Admin Updated"
