import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID

from app.db.session import Base


class User(Base):
    """Модель SQLAlchemy для таблицы 'users'."""

    __tablename__ = "users"

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    login: str = Column(String(32), unique=True, index=True, nullable=False)

    password_hash: str = Column(String, nullable=False)

    created_at: datetime = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self):
        """Строковое представление объекта для отладки."""
        return f"<User(login='{self.login}')>"
