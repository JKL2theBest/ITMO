import pytest
from httpx import AsyncClient
import uuid

pytestmark = pytest.mark.asyncio


async def test_invalid_token_format(client: AsyncClient):
    """Тест: запрос с некорректным форматом токена возвращает 401."""
    headers = {"Authorization": "NotBearer at all"}
    response = await client.get("/api/v1/users/", headers=headers)
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


async def test_token_for_non_existent_user(client: AsyncClient, mocker):
    """Тест: токен для удаленного/несуществующего юзера возвращает 401."""
    mocker.patch("jwt.decode", return_value={"sub": str(uuid.uuid4())})

    headers = {"Authorization": "Bearer some_valid_jwt_structure"}
    response = await client.get("/api/v1/users/", headers=headers)

    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]
