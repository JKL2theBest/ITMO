import pytest
from httpx import AsyncClient

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


async def test_update_own_profile(user_client: AsyncClient):
    """Тест: пользователь может обновить свой собственный профиль."""
    my_id = user_client.user_data["id"]
    new_name = "New Name For Me"

    update_response = await user_client.patch(
        f"/api/v1/users/{my_id}", json={"name": new_name}
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == new_name


async def test_update_other_profile_forbidden(
    user_client: AsyncClient, author_client: AsyncClient
):
    """Тест: обычный пользователь не может обновить профиль другого пользователя."""
    author_id = author_client.user_data["id"]
    response = await user_client.patch(
        f"/api/v1/users/{author_id}", json={"name": "Hacked Name"}
    )
    assert response.status_code == 403


async def test_admin_can_update_and_delete_user(
    admin_client: AsyncClient, user_client: AsyncClient
):
    """Тест: админ может обновлять и удалять других пользователей."""
    user_id_to_modify = user_client.user_data["id"]

    # 1. Проверяем обновление от имени админа
    update_response = await admin_client.patch(
        f"/api/v1/users/{user_id_to_modify}", json={"name": "Admin Updated Name"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Admin Updated Name"

    # 2. Проверяем удаление от имени админа
    delete_response = await admin_client.delete(f"/api/v1/users/{user_id_to_modify}")
    assert delete_response.status_code == 204

    # 3. Убеждаемся, что пользователь удален (админ делает запрос)
    get_response = await admin_client.get(f"/api/v1/users/{user_id_to_modify}")
    assert get_response.status_code == 404
