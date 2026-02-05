import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def news_for_comments(author_client: AsyncClient) -> dict:
    """Фикстура для создания новости, к которой будут добавляться комментарии."""
    response = await author_client.post(
        "/api/v1/news/",
        json={"title": "News for commenting", "content": {}},
    )
    assert response.status_code == 201
    return response.json()


async def test_any_user_can_create_comment(
    user_client: AsyncClient, news_for_comments: dict
):
    """Тест: любой авторизованный пользователь может создать комментарий."""
    response = await user_client.post(
        "/api/v1/comments/",
        json={
            "text": "A comment from a simple user",
            "news_id": news_for_comments["id"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["text"] == "A comment from a simple user"
    assert data["author"]["id"] == user_client.user_data["id"]


async def test_get_comments_unauthorized(client: AsyncClient):
    """Тест: неавторизованный пользователь не может получить комментарии."""
    response = await client.get("/api/v1/comments/")
    assert response.status_code == 401


@pytest.fixture
async def created_comment(user_client: AsyncClient, news_for_comments: dict) -> dict:
    """Фикстура для создания комментария (от имени USER) для тестов обновления/удаления."""
    response = await user_client.post(
        "/api/v1/comments/",
        json={
            "text": "Test Comment for Ownership",
            "news_id": news_for_comments["id"],
        },
    )
    assert response.status_code == 201
    return response.json()


async def test_user_can_update_own_comment(
    user_client: AsyncClient, created_comment: dict
):
    """Тест: пользователь может обновить свой комментарий."""
    comment_id = created_comment["id"]
    response = await user_client.patch(
        f"/api/v1/comments/{comment_id}", json={"text": "Updated by Owner"}
    )
    assert response.status_code == 200
    assert response.json()["text"] == "Updated by Owner"


async def test_author_cannot_update_other_comment(
    author_client: AsyncClient, user_client: AsyncClient, news_for_comments: dict
):
    """Тест: другой пользователь (даже автор) не может обновить чужой комментарий."""
    # 1. user_client создает комментарий
    comment_response = await user_client.post(
        "/api/v1/comments/",
        json={"text": "A user's comment", "news_id": news_for_comments["id"]},
    )
    assert comment_response.status_code == 201
    comment_id = comment_response.json()["id"]

    # 2. author_client пытается его изменить
    response = await author_client.patch(
        f"/api/v1/comments/{comment_id}", json={"text": "Hacked Comment"}
    )
    assert response.status_code == 403


async def test_admin_can_update_other_comment(
    admin_client: AsyncClient, created_comment: dict
):
    """Тест: админ может обновить чужой комментарий."""
    comment_id = created_comment["id"]
    response = await admin_client.patch(
        f"/api/v1/comments/{comment_id}", json={"text": "Updated by Admin"}
    )
    assert response.status_code == 200
    assert response.json()["text"] == "Updated by Admin"


async def test_user_can_delete_own_comment(
    user_client: AsyncClient, news_for_comments: dict
):
    """Тест: пользователь может удалить свой комментарий."""
    response = await user_client.post(
        "/api/v1/comments/",
        json={"text": "To Be Deleted", "news_id": news_for_comments["id"]},
    )
    comment_id = response.json()["id"]

    delete_response = await user_client.delete(f"/api/v1/comments/{comment_id}")
    assert delete_response.status_code == 204

    get_response = await user_client.get(f"/api/v1/comments/{comment_id}")
    assert get_response.status_code == 404


async def test_author_cannot_delete_other_comment(
    author_client: AsyncClient, user_client: AsyncClient, news_for_comments: dict
):
    """Тест: другой пользователь не может удалить чужой комментарий."""
    # 1. user_client создает комментарий
    comment_response = await user_client.post(
        "/api/v1/comments/",
        json={"text": "Another user's comment", "news_id": news_for_comments["id"]},
    )
    assert comment_response.status_code == 201
    comment_id = comment_response.json()["id"]

    # 2. author_client пытается его удалить
    response = await author_client.delete(f"/api/v1/comments/{comment_id}")
    assert response.status_code == 403


async def test_admin_can_delete_other_comment(
    admin_client: AsyncClient, created_comment: dict
):
    """Тест: админ может удалить чужой комментарий."""
    comment_id = created_comment["id"]
    response = await admin_client.delete(f"/api/v1/comments/{comment_id}")
    assert response.status_code == 204
