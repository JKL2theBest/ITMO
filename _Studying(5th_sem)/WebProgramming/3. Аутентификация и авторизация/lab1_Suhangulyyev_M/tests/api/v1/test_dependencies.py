import pytest
from httpx import AsyncClient
from uuid import uuid4

pytestmark = pytest.mark.asyncio


async def test_invalid_token_format(client: AsyncClient):
    """Тест: запрос с некорректным форматом токена возвращает 401."""
    response = await client.get("/api/v1/users/")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


async def test_token_for_non_existent_user(client: AsyncClient, mocker):
    """Тест: токен для удаленного/несуществующего юзера возвращает 401."""
    # Мокаем jwt.decode, чтобы он возвращал ID несуществующего пользователя
    mocker.patch("jose.jwt.decode", return_value={"sub": str(uuid4())})

    headers = {"Authorization": "Bearer faketoken"}
    response = await client.get("/api/v1/users/", headers=headers)
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]


async def test_get_non_existent_object_404(author_client: AsyncClient):
    """Тест: запрос несуществующего объекта по ID возвращает 404."""
    non_existent_uuid = uuid4()
    response = await author_client.get(f"/api/v1/news/{non_existent_uuid}")
    assert response.status_code == 404
