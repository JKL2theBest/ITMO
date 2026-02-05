from datetime import datetime, timedelta, timezone
from typing import Any
from jose import jwt
from argon2 import PasswordHasher
from app.core.config import settings
import secrets

ph = PasswordHasher()


def hash_password(password: str) -> str:
    """Хеширует пароль с использованием Argon2."""
    return ph.hash(password)


def verify_password(hashed_password: str, plain_password: str) -> bool:
    """Сравнение хеша."""
    try:
        return ph.verify(hashed_password, plain_password)
    except Exception:
        return False


def create_access_token(subject: Any, expires_delta: timedelta | None = None) -> str:
    """JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token() -> str:
    """Генерирует безопасный случайный токен."""
    return secrets.token_hex(32)
