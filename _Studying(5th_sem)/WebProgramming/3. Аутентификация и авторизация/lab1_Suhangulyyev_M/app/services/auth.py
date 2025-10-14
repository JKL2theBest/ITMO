from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_sso.sso.base import OpenID
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.sqlalchemy.user import UserRepository


class AuthService:
    """Сервис для всей логики, связанной с аутентификацией."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def login(
        self,
        session: AsyncSession,
        form_data: OAuth2PasswordRequestForm,
        user_agent: str | None,
    ) -> dict:
        """Аутентификация пользователя и создание токенов."""
        user = await self.user_repo.get_by_email(form_data.username)
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

        return await self._create_tokens(
            user=user, session=session, user_agent=user_agent
        )

    async def refresh_token(self, session: AsyncSession, refresh_token: str) -> dict:
        """Обновление access-токена с помощью refresh-токена."""
        query = select(RefreshToken).where(RefreshToken.refresh_token == refresh_token)
        result = await session.execute(query)
        found_token = result.scalars().first()

        if not found_token:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        if found_token.expires_at < datetime.now(timezone.utc):
            await session.delete(found_token)
            await session.commit()
            raise HTTPException(status_code=401, detail="Refresh token has expired")

        user = await self.user_repo.get_by_id(found_token.user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        await session.delete(found_token)

        return await self._create_tokens(
            user=user, session=session, user_agent=found_token.user_agent
        )

    async def logout(self, session: AsyncSession, refresh_token: str) -> None:
        """Выход из системы путем удаления refresh-токена."""
        query = delete(RefreshToken).where(RefreshToken.refresh_token == refresh_token)
        await session.execute(query)
        await session.commit()

    async def handle_sso_callback(
        self, session: AsyncSession, user_info: OpenID, user_agent: str | None
    ) -> dict:
        """Обработка коллбэка от SSO-провайдера (например, GitHub)."""
        email = user_info.email
        if not email:
            raise HTTPException(
                status_code=400, detail="Email not provided by SSO provider"
            )

        user = await self.user_repo.get_by_email(email)

        if not user:
            user = User(
                email=email,
                name=user_info.display_name or email.split("@")[0],
                avatar_url=user_info.picture,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

        return await self._create_tokens(
            user=user, session=session, user_agent=user_agent
        )

    async def _create_tokens(
        self, user: User, session: AsyncSession, user_agent: str | None
    ) -> dict:
        """Вспомогательный метод для создания access и refresh токенов."""
        access_token = create_access_token(subject=user.id)
        refresh_token_str = create_refresh_token()
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        new_refresh_token = RefreshToken(
            user_id=user.id,
            refresh_token=refresh_token_str,
            expires_at=datetime.now(timezone.utc) + expires_delta,
            user_agent=user_agent,
        )
        session.add(new_refresh_token)
        await session.commit()

        return {"access_token": access_token, "refresh_token": refresh_token_str}
