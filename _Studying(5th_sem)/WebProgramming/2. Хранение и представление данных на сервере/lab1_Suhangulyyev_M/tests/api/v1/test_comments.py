import pytest
from httpx import AsyncClient
from uuid import uuid4

pytestmark = pytest.mark.asyncio


# --- ФИКСТУРЫ ---


@pytest.fixture
async def author(async_client: AsyncClient) -> dict:
    user_data = {"name": "Comment Author", "email": f"{uuid4()}@example.com"}
    response = await async_client.post("/api/v1/users/", json=user_data)
    return response.json()


@pytest.fixture
async def news_item(async_client: AsyncClient) -> dict:
    author_data = {
        "name": "News Author",
        "email": f"{uuid4()}@example.com",
        "is_verified_author": True,
    }
    author_response = await async_client.post("/api/v1/users/", json=author_data)
    author_id = author_response.json()["id"]

    news_data = {
        "title": "News to comment",
        "content": {"body": "Content"},
        "author_id": author_id,
    }
    news_response = await async_client.post("/api/v1/news/", json=news_data)
    return news_response.json()


@pytest.fixture
async def created_comment(
    async_client: AsyncClient, author: dict, news_item: dict
) -> dict:
    comment_data = {
        "text": "A test comment",
        "author_id": author["id"],
        "news_id": news_item["id"],
    }
    response = await async_client.post("/api/v1/comments/", json=comment_data)
    return response.json()


# --- ТЕСТЫ ---


async def test_create_comment_success(
    async_client: AsyncClient, author: dict, news_item: dict
):
    """Тест создания комментария."""
    comment_data = {
        "text": "This is a great article!",
        "author_id": author["id"],
        "news_id": news_item["id"],
    }
    response = await async_client.post("/api/v1/comments/", json=comment_data)

    assert response.status_code == 201
    data = response.json()
    assert data["text"] == comment_data["text"]
    assert data["author"]["id"] == author["id"]


async def test_create_comment_nonexistent_author(
    async_client: AsyncClient, news_item: dict
):
    """Тест создания комментария с несуществующим автором."""
    comment_data = {
        "text": "A comment",
        "author_id": str(uuid4()),
        "news_id": news_item["id"],
    }
    response = await async_client.post("/api/v1/comments/", json=comment_data)

    assert response.status_code == 404
    assert "Comment author not found" in response.json()["detail"]


async def test_create_comment_nonexistent_news(async_client: AsyncClient, author: dict):
    """Тест создания комментария к несуществующей новости."""
    comment_data = {
        "text": "A comment",
        "author_id": author["id"],
        "news_id": str(uuid4()),
    }
    response = await async_client.post("/api/v1/comments/", json=comment_data)

    assert response.status_code == 404
    assert "News for commenting not found" in response.json()["detail"]


async def test_get_comment_by_id(async_client: AsyncClient, created_comment: dict):
    """Тест получения комментария по ID."""
    response = await async_client.get(f"/api/v1/comments/{created_comment['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created_comment["id"]


async def test_update_comment_partial_success(
    async_client: AsyncClient, created_comment: dict
):
    """Тест частичного обновления комментария."""
    update_data = {"text": "I have updated my opinion."}
    response = await async_client.patch(
        f"/api/v1/comments/{created_comment['id']}", json=update_data
    )

    assert response.status_code == 200
    assert response.json()["text"] == update_data["text"]


async def test_delete_comment_success(async_client: AsyncClient, created_comment: dict):
    """Тест удаления комментария."""
    response = await async_client.delete(f"/api/v1/comments/{created_comment['id']}")
    assert response.status_code == 204

    get_response = await async_client.get(f"/api/v1/comments/{created_comment['id']}")
    assert get_response.status_code == 404


async def test_get_all_comments(async_client: AsyncClient, created_comment: dict):
    """Тест получения списка комментариев."""
    response = await async_client.get("/api/v1/comments/")

    assert response.status_code == 200
    comment_list = response.json()
    assert isinstance(comment_list, list)
    assert len(comment_list) >= 1
    assert any(c["id"] == created_comment["id"] for c in comment_list)


@pytest.mark.parametrize(
    "method, endpoint_template",
    [
        ("GET", "/api/v1/comments/{}"),
        ("PATCH", "/api/v1/comments/{}"),
        ("DELETE", "/api/v1/comments/{}"),
    ],
)
async def test_comment_not_found(
    async_client: AsyncClient, method: str, endpoint_template: str
):
    """Тест ошибок 404."""
    non_existent_id = uuid4()
    url = endpoint_template.format(non_existent_id)

    # Для PATCH - json
    kwargs = {"json": {"text": "..."}} if method == "PATCH" else {}

    response = await async_client.request(method, url, **kwargs)

    assert response.status_code == 404
