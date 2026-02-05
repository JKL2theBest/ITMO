import uuid
import datetime
from typing import TYPE_CHECKING  # для ruff
from sqlalchemy import DateTime, func, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


# для ruff
if TYPE_CHECKING:
    from .user import User
    from .news import News


class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[uuid.UUID] = mapped_column(
        pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    news_id: Mapped[uuid.UUID] = mapped_column(
        pgUUID(as_uuid=True), ForeignKey("news.id")
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        pgUUID(as_uuid=True), ForeignKey("users.id")
    )

    news: Mapped["News"] = relationship(back_populates="comments")
    author: Mapped["User"] = relationship(back_populates="comments")
