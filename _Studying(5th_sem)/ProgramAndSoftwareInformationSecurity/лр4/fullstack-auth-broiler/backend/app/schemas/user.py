import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


# --- Схемы для API (взаимодействие с внешним миром) ---
class UserBase(BaseModel):
    """Базовая схема пользователя с общими полями."""

    login: str = Field(
        min_length=3,
        max_length=32,
        description="Уникальный логин пользователя",
    )


class UserCreateRequest(UserBase):
    """Схема для валидации данных при регистрации пользователя (входные данные от клиента)."""

    password: str = Field(min_length=8, description="Пароль пользователя")

    @field_validator("login")
    @classmethod
    def validate_login(cls, value: str) -> str:
        """
        Валидатор логина. Разрешает только безопасные символы.
        """
        if not re.match(r"^[a-zA-Z0-9_.-]+$", value):
            raise ValueError(
                "Login must contain only latin letters, numbers, and symbols: . _ -"
            )
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """
        Валидатор сложности пароля.
        """
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?:{}|<>]", value):
            raise ValueError("Password must contain at least one special character")
        return value


class UserLoginRequest(BaseModel):
    """Схема для валидации данных при входе пользователя."""

    login: str = Field(..., min_length=1, description="Логин пользователя")
    password: str = Field(..., min_length=1, description="Пароль пользователя")


class UserPublic(UserBase):
    """
    Схема для публичного представления пользователя (ответ API).
    """

    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Схема для ответа с JWT токеном."""

    access_token: str
    token_type: str = "bearer"


# --- Схемы для внутреннего использования (между сервисами и репозиториями) ---
class UserCreateInternal(UserBase):
    """
    Схема для передачи данных в репозиторий для создания пользователя.
    """

    password_hash: str
