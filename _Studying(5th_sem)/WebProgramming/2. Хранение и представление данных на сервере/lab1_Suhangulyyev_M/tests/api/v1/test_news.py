import pytest
from httpx import AsyncClient
from uuid import uuid4

pytestmark = pytest.mark.asyncio


# --- ФИКСТУРЫ ---


@pytest.fixture
async def verified_author(async_client: AsyncClient) -> dict:
    """Создает верифицированного автора."""
    unique_email = f"{uuid4()}@author.com"
    user_data = {
        "name": "Verified Author",
        "email": unique_email,
        "is_verified_author": True,
    }
    response = await async_client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
async def unverified_author(async_client: AsyncClient) -> dict:
    """Создает неверифицированного автора."""
    unique_email = f"{uuid4()}@unverified.com"
    user_data = {
        "name": "Unverified Author",
        "email": unique_email,
        "is_verified_author": False,
    }
    response = await async_client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
async def created_news(async_client: AsyncClient, verified_author: dict) -> dict:
    """Создает новость, зависящую от верифицированного автора."""
    news_data = {
        "title": "Pre-existing News",
        "content": {"body": "Some content"},
        "author_id": verified_author["id"],
    }
    response = await async_client.post("/api/v1/news/", json=news_data)
    assert response.status_code == 201
    return response.json()


# --- ТЕСТЫ ---


async def test_create_news_success(async_client: AsyncClient, verified_author: dict):
    """Тест создания новости верифицированным автором."""
    news_data = {
        "title": "A New Article",
        "content": {"body": "Details here"},
        "author_id": verified_author["id"],
    }
    response = await async_client.post("/api/v1/news/", json=news_data)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == news_data["title"]
    assert data["author"]["id"] == verified_author["id"]


async def test_create_news_by_unverified_author(
    async_client: AsyncClient, unverified_author: dict
):
    """Тест создания новости неверифицированным автором."""
    news_data = {
        "title": "Forbidden News",
        "content": {},
        "author_id": unverified_author["id"],
    }
    response = await async_client.post("/api/v1/news/", json=news_data)

    assert response.status_code == 403
    assert "not verified like an author" in response.json()["detail"]


async def test_create_news_with_nonexistent_author(async_client: AsyncClient):
    """Тест создания новости с несуществующим автором."""
    news_data = {"title": "Orphan News", "content": {}, "author_id": str(uuid4())}
    response = await async_client.post("/api/v1/news/", json=news_data)

    assert response.status_code == 404
    assert "Author does not exist" in response.json()["detail"]


async def test_get_all_news(async_client: AsyncClient, created_news: dict):
    """Тест получения списка новостей."""
    response = await async_client.get("/api/v1/news/")
    assert response.status_code == 200
    news_list = response.json()
    assert isinstance(news_list, list)
    assert any(item["id"] == created_news["id"] for item in news_list)


async def test_get_news_by_id_success(async_client: AsyncClient, created_news: dict):
    """Тест получения новости по ID."""
    response = await async_client.get(f"/api/v1/news/{created_news['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created_news["id"]


async def test_update_news_partial_success(
    async_client: AsyncClient, created_news: dict
):
    """Тест частичного обновления новости."""
    update_data = {"title": "Updated Title Only"}
    response = await async_client.patch(
        f"/api/v1/news/{created_news['id']}", json=update_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["content"] == created_news["content"]
    assert data["id"] == created_news["id"]


async def test_delete_news_success(async_client: AsyncClient, created_news: dict):
    """Тест удаления новости."""
    delete_response = await async_client.delete(f"/api/v1/news/{created_news['id']}")
    assert delete_response.status_code == 204

    get_response = await async_client.get(f"/api/v1/news/{created_news['id']}")
    assert get_response.status_code == 404


@pytest.mark.parametrize(
    "method, endpoint_template",
    [
        ("GET", "/api/v1/news/{}"),
        ("PATCH", "/api/v1/news/{}"),
        ("DELETE", "/api/v1/news/{}"),
    ],
)
async def test_news_not_found(
    async_client: AsyncClient, method: str, endpoint_template: str
):
    """Тест ошибки 404."""
    non_existent_id = uuid4()
    url = endpoint_template.format(non_existent_id)

    kwargs = {"json": {"title": "..."}} if method == "PATCH" else {}

    response = await async_client.request(method, url, **kwargs)

    assert response.status_code == 404
