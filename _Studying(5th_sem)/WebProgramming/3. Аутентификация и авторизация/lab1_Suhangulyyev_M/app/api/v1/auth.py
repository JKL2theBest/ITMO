from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_sso.sso.github import GithubSSO
from pydantic import BaseModel
from sqlalchemy import delete, select

from app.api.dependencies import (
    CurrentUserDep,
    DBSession,
    UserRepoDep,
    UserServiceDep,
)
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.refresh_token import RefreshTokenResponse
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def get_github_sso() -> GithubSSO:
    """Возвращает экземпляр GithubSSO с настройками из .env."""
    return GithubSSO(
        settings.GITHUB_CLIENT_ID,
        settings.GITHUB_CLIENT_SECRET,
        settings.GITHUB_CALLBACK_URL,
    )


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


github_sso = GithubSSO(
    settings.GITHUB_CLIENT_ID,
    settings.GITHUB_CLIENT_SECRET,
    settings.GITHUB_CALLBACK_URL,
)


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(user_data: UserCreate, service: UserServiceDep):
    return await service.create_user(user_data)


@router.post("/login", response_model=TokenResponse)
async def login_for_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_repo: UserRepoDep,
    session: DBSession,
):
    user = await user_repo.get_by_email(form_data.username)
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not verify_password(user.hashed_password, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(subject=user.id)
    refresh_token_str = create_refresh_token()
    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    new_refresh_token = RefreshToken(
        user_id=user.id,
        refresh_token=refresh_token_str,
        expires_at=datetime.now(timezone.utc) + expires_delta,
        user_agent=request.headers.get("user-agent"),
    )
    session.add(new_refresh_token)
    await session.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token_str)


@router.get("/github/login")
async def github_login(
    github_sso: Annotated[GithubSSO, Depends(get_github_sso)],
):
    """Генерирует URL для редиректа на GitHub для аутентификации."""
    async with github_sso as sso:
        return await sso.get_login_redirect()


@router.get("/github/callback", response_model=TokenResponse)
async def github_callback(
    request: Request,
    user_repo: UserRepoDep,
    session: DBSession,
    github_sso: Annotated[GithubSSO, Depends(get_github_sso)],
):
    """Обрабатывает коллбэк от GitHub после аутентификации."""
    async with github_sso as sso:
        user_info = await sso.verify_and_process(request)

    if not user_info:
        raise HTTPException(status_code=400, detail="GitHub login failed")

    email = user_info.email
    user = await user_repo.get_by_email(email)

    if not user:
        user = User(
            email=email,
            name=user_info.display_name or email.split("@")[0],
            avatar_url=user_info.picture,
            # Пароля нет, роль по умолчанию - USER
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    access_token = create_access_token(subject=user.id)
    refresh_token_str = create_refresh_token()
    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    new_refresh_token = RefreshToken(
        user_id=user.id,
        refresh_token=refresh_token_str,
        expires_at=datetime.now(timezone.utc) + expires_delta,
        user_agent=request.headers.get("user-agent"),
    )
    session.add(new_refresh_token)
    await session.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token_str)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    request: RefreshTokenRequest,
    session: DBSession,
):
    query = select(RefreshToken).where(
        RefreshToken.refresh_token == request.refresh_token
    )
    result = await session.execute(query)
    found_token = result.scalars().first()

    if not found_token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if found_token.expires_at < datetime.now(timezone.utc):
        await session.delete(found_token)
        await session.commit()
        raise HTTPException(status_code=401, detail="Refresh token has expired")

    # Ротация токенов
    await session.delete(found_token)

    access_token = create_access_token(subject=found_token.user_id)

    refresh_token_str = create_refresh_token()
    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    user_agent = found_token.user_agent

    new_refresh_token = RefreshToken(
        user_id=found_token.user_id,
        refresh_token=refresh_token_str,
        expires_at=datetime.now(timezone.utc) + expires_delta,
        user_agent=user_agent,
    )
    session.add(new_refresh_token)
    await session.commit()

    return TokenResponse(access_token=access_token, refresh_token=refresh_token_str)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: RefreshTokenRequest,
    session: DBSession,
):
    query = delete(RefreshToken).where(
        RefreshToken.refresh_token == request.refresh_token
    )
    await session.execute(query)
    await session.commit()


@router.get("/sessions/me", response_model=list[RefreshTokenResponse])
async def get_my_sessions(
    current_user: CurrentUserDep,
    session: DBSession,
):
    query = select(RefreshToken).where(RefreshToken.user_id == current_user.id)
    result = await session.execute(query)
    return result.scalars().all()
