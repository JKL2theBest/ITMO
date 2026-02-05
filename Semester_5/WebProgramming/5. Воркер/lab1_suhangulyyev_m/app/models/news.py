import uuid
import datetime
from typing import TYPE_CHECKING  # для ruff
from sqlalchemy import String, DateTime, func, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

# для ruff
if TYPE_CHECKING:
    from .user import User
    from .comment import Comment


class News(Base):
    __tablename__ = "news"
    id: Mapped[uuid.UUID] = mapped_column(
        pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(100), index=True)
    content: Mapped[dict] = mapped_column(JSON)
    published_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    cover_image_url: Mapped[str | None] = mapped_column(String(255))
    author_id: Mapped[uuid.UUID] = mapped_column(
        pgUUID(as_uuid=True), ForeignKey("users.id")
    )

    author: Mapped["User"] = relationship(back_populates="news")
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="news", cascade="all, delete-orphan"
    )
