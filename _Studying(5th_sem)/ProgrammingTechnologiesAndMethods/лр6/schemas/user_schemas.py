"""
Модуль Pydantic-схем для валидации и структурирования данных.

Определяет структуры данных для создания, обновления и представления
сущности "Пользователь", обеспечивая строгую типизацию и валидацию
на уровне приложения.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    """Базовая схема с общими полями пользователя."""

    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    """Схема для создания нового пользователя (входные данные)."""

    password: str = Field(..., min_length=8)
    role_name: str = Field("user", description="Название роли при регистрации")


class UserPublic(UserBase):
    """
    Схема для публичного представления пользователя (выходные данные).
    Не содержит пароль или другую чувствительную информацию.
    """

    id: uuid.UUID
    role_name: str
    created_at: datetime

    # Указывает Pydantic, что модель может быть создана из атрибутов объекта SQLAlchemy
    model_config = ConfigDict(from_attributes=True)
