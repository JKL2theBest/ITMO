import uuid
import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

if TYPE_CHECKING:
    from .user import User


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        pgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    refresh_token: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )
    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    user_agent: Mapped[str | None] = mapped_column(String)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")
