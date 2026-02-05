import json
from datetime import timedelta, timezone, datetime
from typing import Any

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_sso.sso.base import OpenID
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from app.models.user import User
from app.repositories.sqlalchemy.user import UserRepository


class AuthService:
    """Сервис для всей логики, связанной с аутентификацией, с использованием Redis."""

    def __init__(self, user_repo: UserRepository, redis_client: Redis):
        self.user_repo = user_repo
        self.redis = redis_client

    async def login(
        self,
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
        return await self._create_tokens(user=user, user_agent=user_agent)

    async def refresh_token(self, refresh_token: str) -> dict:
        """Обновление access-токена с помощью refresh-токена из Redis."""
        token_key = f"refresh_token:{refresh_token}"
        session_data_json = await self.redis.get(token_key)

        # Если токена нет, это значит, что он невалиден или истек.
        if not session_data_json:
            raise HTTPException(
                status_code=401, detail="Invalid or expired refresh token"
            )

        session_data = json.loads(session_data_json)
        user = await self.user_repo.get_by_id(session_data["user_id"])

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        # Удаляем старый токен
        await self.redis.delete(token_key)
        user_sessions_key = f"user_sessions:{user.id}"
        await self.redis.srem(user_sessions_key, refresh_token)

        return await self._create_tokens(
            user=user, user_agent=session_data.get("user_agent")
        )

    async def logout(self, refresh_token: str) -> None:
        """Выход из системы путем удаления refresh-токена из Redis."""
        token_key = f"refresh_token:{refresh_token}"
        session_data_json = await self.redis.get(token_key)

        if session_data_json:
            session_data = json.loads(session_data_json)
            user_id = session_data.get("user_id")
            await self.redis.delete(token_key)
            if user_id:
                user_sessions_key = f"user_sessions:{user_id}"
                await self.redis.srem(user_sessions_key, refresh_token)

    async def handle_sso_callback(
        self, session: AsyncSession, user_info: OpenID, user_agent: str | None
    ) -> dict:
        """Обработка коллбэка от SSO-провайдера (ex. GitHub)."""
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

        return await self._create_tokens(user=user, user_agent=user_agent)

    async def get_user_sessions(self, user_id: str) -> list[dict[str, Any]]:
        """Получение активных сессий пользователя из Redis."""
        user_sessions_key = f"user_sessions:{user_id}"
        token_strings = await self.redis.smembers(user_sessions_key)

        sessions_info = []
        for token_str in token_strings:
            session_data_json = await self.redis.get(f"refresh_token:{token_str}")
            if session_data_json:
                session_data = json.loads(session_data_json)
                sessions_info.append(
                    {
                        "refresh_token": token_str,
                        "user_agent": session_data.get("user_agent"),
                        "created_at": session_data.get("created_at"),
                    }
                )
        return sessions_info

    async def _create_tokens(self, user: User, user_agent: str | None) -> dict:
        """Вспомогательный метод для создания access и refresh токенов и сохранения в Redis."""
        access_token = create_access_token(subject=user.id)
        refresh_token_str = create_refresh_token()
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        session_data = {
            "user_id": str(user.id),
            "user_agent": user_agent,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # Сохраняем основную информацию о сессии, передавая `ex` для установки TTL
        await self.redis.set(
            name=f"refresh_token:{refresh_token_str}",
            value=json.dumps(session_data),
            ex=expires_delta,
        )

        # Добавляем токен в множество сессий пользователя
        user_sessions_key = f"user_sessions:{user.id}"
        await self.redis.sadd(user_sessions_key, refresh_token_str)
        await self.redis.expire(user_sessions_key, expires_delta)

        return {"access_token": access_token, "refresh_token": refresh_token_str}
