import pytest
from httpx import AsyncClient
from uuid import uuid4

pytestmark = pytest.mark.asyncio

# --- ТЕСТЫ ---


async def test_create_user_success(async_client: AsyncClient):
    """Тест создания пользователя."""
    user_data = {"name": "Test User", "email": "test@example.com"}
    response = await async_client.post("/api/v1/users/", json=user_data)

    assert response.status_code == 201
    response_data = response.json()
    assert response_data["email"] == user_data["email"]
    assert response_data["name"] == user_data["name"]
    assert "id" in response_data


async def test_create_user_duplicate_email(async_client: AsyncClient):
    """Тест создания пользователя с существующим email."""
    user_data = {"name": "Another Test User", "email": "another@example.com"}
    await async_client.post("/api/v1/users/", json=user_data)
    response = await async_client.post("/api/v1/users/", json=user_data)

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


async def test_get_user_success(async_client: AsyncClient):
    """Тест получения пользователя по ID."""
    user_data = {"name": "Get Me User", "email": "getme@example.com"}
    create_response = await async_client.post("/api/v1/users/", json=user_data)
    user_id = create_response.json()["id"]

    get_response = await async_client.get(f"/api/v1/users/{user_id}")

    assert get_response.status_code == 200
    response_data = get_response.json()
    assert response_data["id"] == user_id
    assert response_data["email"] == user_data["email"]


async def test_update_user_partial_success(async_client: AsyncClient):
    """Тест частичного обновления пользователя."""
    user_data = {
        "name": "User to Update",
        "email": "update@example.com",
        "is_verified_author": False,
    }
    create_response = await async_client.post("/api/v1/users/", json=user_data)
    user_id = create_response.json()["id"]

    update_data = {"name": "Updated Name Only"}
    update_response = await async_client.patch(
        f"/api/v1/users/{user_id}", json=update_data
    )

    assert update_response.status_code == 200
    updated_user = update_response.json()
    assert updated_user["name"] == "Updated Name Only"
    assert updated_user["email"] == "update@example.com"
    assert updated_user["is_verified_author"] is False


async def test_delete_user_success(async_client: AsyncClient):
    """Тест удаления пользователя."""
    user_data = {"name": "User to Delete", "email": "delete@example.com"}
    create_response = await async_client.post("/api/v1/users/", json=user_data)
    user_id = create_response.json()["id"]

    delete_response = await async_client.delete(f"/api/v1/users/{user_id}")
    assert delete_response.status_code == 204

    get_response = await async_client.get(f"/api/v1/users/{user_id}")
    assert get_response.status_code == 404


async def test_get_all_users(async_client: AsyncClient):
    """Тест получения и пагинации списка пользователей."""
    await async_client.post(
        "/api/v1/users/", json={"name": "User A", "email": "a@test.com"}
    )
    await async_client.post(
        "/api/v1/users/", json={"name": "User B", "email": "b@test.com"}
    )
    await async_client.post(
        "/api/v1/users/", json={"name": "User C", "email": "c@test.com"}
    )

    response = await async_client.get("/api/v1/users/?skip=1&limit=1")
    assert response.status_code == 200
    user_list = response.json()
    assert len(user_list) == 1
    assert user_list[0]["name"] == "User B"


@pytest.mark.parametrize(
    "method, endpoint_template",
    [
        ("GET", "/api/v1/users/{}"),
        ("PATCH", "/api/v1/users/{}"),
        ("DELETE", "/api/v1/users/{}"),
    ],
)
async def test_user_not_found(
    async_client: AsyncClient, method: str, endpoint_template: str
):
    """Тест ошибки 404."""
    non_existent_id = uuid4()
    url = endpoint_template.format(non_existent_id)

    kwargs = {"json": {"name": "..."}} if method == "PATCH" else {}

    response = await async_client.request(method, url, **kwargs)

    assert response.status_code == 404
