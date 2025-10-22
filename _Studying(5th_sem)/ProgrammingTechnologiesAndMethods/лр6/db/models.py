"""
Модуль определения моделей данных SQLAlchemy.

В данном модуле описываются структуры таблиц базы данных в виде
Python-классов, соответствующих требованиям ГОСТ 19.701-90 (ИСО 5807-85)
в части описания структур данных.
"""

import uuid
from datetime import datetime
from typing import List

from sqlalchemy import DateTime, ForeignKey, String, func, Boolean
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship

# Базовый класс для всех декларативных моделей.
Base = declarative_base()


class User(Base):
    """
    Модель данных для таблицы 'users'.

    Представляет сущность "Пользователь" в системе.

    Атрибуты:
        id (uuid.UUID): Уникальный идентификатор пользователя (первичный ключ).
        username (str): Имя пользователя, уникальное в системе.
        hashed_password (str): Хеш пароля пользователя, вычисленный с солью.
        created_at (datetime): Дата и время создания записи о пользователе.
        role_id (int): Внешний ключ, связывающий пользователя с ролью.
        role (Mapped["Role"]): Отношение "многие-к-одному" к модели Role.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))

    mfa_secret: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    role: Mapped["Role"] = relationship(back_populates="users")
    sessions: Mapped[List["Session"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        """Возвращает строковое представление объекта для отладки."""
        return f"<User(username='{self.username}', role='{self.role.name}')>"


class Role(Base):
    """
    Модель данных для таблицы 'roles'.

    Представляет сущность "Роль", определяющую права доступа пользователя.

    Атрибуты:
        id (int): Уникальный идентификатор роли (первичный ключ).
        name (str): Название роли (например, 'admin', 'user', 'guest').
        users (Mapped[List["User"]]): Отношение "один-ко-многим" к модели User.
    """

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    users: Mapped[List["User"]] = relationship(back_populates="role")

    def __repr__(self) -> str:
        """Возвращает строковое представление объекта для отладки."""
        return f"<Role(name='{self.name}')>"


class Session(Base):
    """
    Модель данных для таблицы 'sessions'.

    Представляет активную сессию пользователя, связанную с токеном.

    Атрибуты:
        id (uuid.UUID): Уникальный идентификатор сессии.
        token (str): Уникальный сессионный токен.
        expires_at (datetime): Дата и время истечения срока действия сессии.
        user_id (uuid.UUID): Внешний ключ, связывающий сессию с пользователем.
        user (Mapped["User"]): Отношение "многие-к-одному" к модели User.
    """

    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    user: Mapped["User"] = relationship(back_populates="sessions")

    def __repr__(self) -> str:
        return f"<Session(user='{self.user.username}', expires_at='{self.expires_at}')>"
