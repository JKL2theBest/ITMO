from uuid import uuid4
import pytest
from httpx import AsyncClient
from app.schemas.role import UserRole

pytestmark = pytest.mark.asyncio


async def test_get_users_unauthorized(client: AsyncClient):
    """Тест: неавторизованный пользователь не может получить список пользователей."""
    response = await client.get("/api/v1/users/")
    assert response.status_code == 401


async def test_get_users_authorized(user_client: AsyncClient):
    """Тест: авторизованный пользователь может получить список пользователей."""
    response = await user_client.get("/api/v1/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_update_own_profile(authenticated_client_factory):
    """Тест: пользователь может обновить свой собственный профиль."""
    email = f"{uuid4()}@test.com"
    password = "password123"

    client, _ = await authenticated_client_factory(  # <-- Распаковка
        UserRole.USER, email=email, password=password
    )

    users_list_response = await client.get("/api/v1/users/")
    assert users_list_response.status_code == 200

    my_data = next(
        (user for user in users_list_response.json() if user["email"] == email), None
    )
    assert my_data is not None
    my_id = my_data["id"]

    update_response = await client.patch(
        f"/api/v1/users/{my_id}", json={"name": "New Name"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "New Name"


async def test_update_other_profile_forbidden(authenticated_client_factory):
    """Тест: обычный пользователь не может обновить профиль другого пользователя."""
    user_client, _ = await authenticated_client_factory(UserRole.USER)
    author_client, author_data_dict = await authenticated_client_factory(
        UserRole.VERIFIED_AUTHOR
    )

    response = await user_client.patch(
        f"/api/v1/users/{author_data_dict['id']}", json={"name": "Hacked Name"}
    )
    assert response.status_code == 403


async def test_admin_can_update_and_delete_user(authenticated_client_factory):
    """Тест: админ может обновлять и удалять других пользователей."""
    admin_client, _ = await authenticated_client_factory(UserRole.ADMIN)
    user_client, user_data_dict = await authenticated_client_factory(UserRole.USER)

    user_id = user_data_dict["id"]

    update_response = await admin_client.patch(
        f"/api/v1/users/{user_id}", json={"name": "Admin Updated Name"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Admin Updated Name"

    delete_response = await admin_client.delete(f"/api/v1/users/{user_id}")
    assert delete_response.status_code == 204

    get_response = await admin_client.get(f"/api/v1/users/{user_id}")
    assert get_response.status_code == 404
