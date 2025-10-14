import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi_sso.sso.base import OpenID
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    "name, email, password, status_code",
    [
        ("test_user", f"{uuid.uuid4()}@test.com", "password123", 201),
        ("test_user_repeat", "user@test.com", "password123", 400),
    ],
)
async def test_register_user(client: AsyncClient, name, email, password, status_code):
    """Тест регистрации: успех и дубликат email."""
    if "repeat" in name:
        await client.post(
            "/api/v1/auth/register",
            json={"name": "first_user", "email": email, "password": password},
        )

    response = await client.post(
        "/api/v1/auth/register",
        json={"name": name, "email": email, "password": password},
    )
    assert response.status_code == status_code
    if status_code == 201:
        assert response.json()["email"] == email


@pytest.mark.parametrize(
    "email, password, status_code, detail",
    [
        ("wrong@user.com", "password123", 401, "Incorrect email or password"),
        ("user@test.com", "wrongpassword", 401, "Incorrect email or password"),
    ],
)
async def test_login_failures(
    client: AsyncClient, email, password, status_code, detail
):
    """Тест неудачных попыток входа."""
    await client.post(
        "/api/v1/auth/register",
        json={"name": "Test User", "email": "user@test.com", "password": "password123"},
    )
    response = await client.post(
        "/api/v1/auth/login", data={"username": email, "password": password}
    )
    assert response.status_code == status_code
    assert detail in response.json()["detail"]


async def test_login_and_get_sessions(user_client: AsyncClient):
    """Тест успешного логина и получения списка сессий."""
    response = await user_client.get("/api/v1/auth/sessions/me")
    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) == 1
    assert "user_agent" in sessions[0]


async def test_refresh_and_logout(user_client: AsyncClient):
    """Тест полного флоу refresh и logout."""
    refresh_token = user_client.refresh_token

    refresh_response = await user_client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()
    new_refresh_token = new_tokens["refresh_token"]

    old_token_response = await user_client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert old_token_response.status_code == 401

    logout_response = await user_client.post(
        "/api/v1/auth/logout", json={"refresh_token": new_refresh_token}
    )
    assert logout_response.status_code == 204

    final_refresh_response = await user_client.post(
        "/api/v1/auth/refresh", json={"refresh_token": new_refresh_token}
    )
    assert final_refresh_response.status_code == 401


async def test_refresh_invalid_token(client: AsyncClient):
    """Тест: попытка рефреша с невалидным токеном."""
    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "invalid_token"}
    )
    assert response.status_code == 401


async def test_github_login_redirect(client: AsyncClient):
    """Тест: ручка логина GitHub возвращает редирект."""
    response = await client.get("/api/v1/auth/github/login", follow_redirects=False)
    assert response.status_code == 303  # ИСПРАВЛЕНО: 307 -> 303


async def test_github_callback_new_user(client: AsyncClient, mocker):
    """Тест коллбэка GitHub для нового пользователя."""
    mock_openid = OpenID(
        id="github_id_123",
        email="new_github_user@test.com",
        display_name="New GitHub User",
    )
    mocker.patch(
        "fastapi_sso.sso.github.GithubSSO.verify_and_process",
        new_callable=AsyncMock,
        return_value=mock_openid,
    )
    response = await client.get(
        "/api/v1/auth/github/callback?code=fakecode&state=fakestate"
    )
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens


async def test_github_callback_existing_user(client: AsyncClient, mocker):
    """Тест коллбэка GitHub для существующего пользователя."""
    existing_email = "existing_github_user@test.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Existing User",
            "email": existing_email,
            "password": "password123",
        },
    )
    mock_openid = OpenID(
        id="github_id_456", email=existing_email, display_name="Existing User"
    )
    mocker.patch(
        "fastapi_sso.sso.github.GithubSSO.verify_and_process",
        new_callable=AsyncMock,
        return_value=mock_openid,
    )
    response = await client.get(
        "/api/v1/auth/github/callback?code=fakecode&state=fakestate"
    )
    assert response.status_code == 200
    tokens = response.json()
    assert "access_token" in tokens


async def test_refresh_with_expired_token(
    client: AsyncClient, db_session_test: AsyncSession
):
    """Тест: попытка рефреша с просроченным токеном."""
    email = f"{uuid.uuid4()}@test.com"
    await client.post(
        "/api/v1/auth/register",
        json={"name": "exp_user", "email": email, "password": "password123"},
    )
    login_response = await client.post(
        "/api/v1/auth/login", data={"username": email, "password": "password123"}
    )
    assert login_response.status_code == 200
    refresh_token = login_response.json()["refresh_token"]

    async with db_session_test as session:
        result = await session.execute(
            select(RefreshToken).where(RefreshToken.refresh_token == refresh_token)
        )
        token_obj = result.scalar_one()
        token_obj.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        await session.commit()

    response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert response.status_code == 401
    assert "Refresh token has expired" in response.json()["detail"]


async def test_github_callback_process_error(client: AsyncClient, mocker):
    """Тест: коллбэк GitHub возвращает ошибку, если verify_and_process вернул None."""
    mocker.patch(
        "fastapi_sso.sso.github.GithubSSO.verify_and_process",
        new_callable=AsyncMock,
        return_value=None,
    )
    response = await client.get(
        "/api/v1/auth/github/callback?code=fakecode&state=fakestate"
    )
    assert response.status_code == 400
    assert "GitHub login failed" in response.json()["detail"]
