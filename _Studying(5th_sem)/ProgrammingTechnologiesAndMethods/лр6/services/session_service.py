"""
Модуль бизнес-логики для управления сессиями пользователей.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Session, User
from core.security import generate_session_token


class SessionService:
    """Сервис для управления сессиями."""

    SESSION_LIFETIME = timedelta(hours=1)  # Сессия живет 1 час

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(self, user: User) -> Session:
        """
        Создает новую сессию для пользователя.

        Args:
            user: Объект пользователя, для которого создается сессия.

        Returns:
            Созданный объект Session.
        """
        now = datetime.now(timezone.utc)
        new_session = Session(
            user_id=user.id,
            token=generate_session_token(),
            expires_at=now + self.SESSION_LIFETIME,
        )
        self.session.add(new_session)
        await self.session.flush()
        await self.session.refresh(new_session)
        return new_session

    async def get_user_by_token(self, token: str) -> Optional[User]:
        """
        Находит пользователя по действующему токену сессии.

        Args:
            token: Сессионный токен.

        Returns:
            Объект User, если токен валиден и не истек, иначе None.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(Session)
            .where(Session.token == token, Session.expires_at > now)
            .options(selectinload(Session.user).selectinload(User.role))
        )
        result = await self.session.execute(stmt)
        session = result.scalar_one_or_none()

        return session.user if session else None

    async def terminate_session(self, token: str) -> bool:
        """
        Завершает сессию по токену (logout).

        Args:
            token: Токен сессии для удаления.

        Returns:
            True, если сессия была найдена и удалена, иначе False.
        """
        stmt = delete(Session).where(Session.token == token)
        result = await self.session.execute(stmt)
        # rowcount > 0 означает, что строка была удалена
        return result.rowcount > 0
