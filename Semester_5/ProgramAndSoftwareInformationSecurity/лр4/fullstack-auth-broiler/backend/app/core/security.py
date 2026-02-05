from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# Создаем контекст Passlib для хеширования паролей.
pwd_context = CryptContext(
    schemes=[settings.HASH_SCHEME],
    deprecated="auto",
    # Настройки для Argon2, загруженные из .env файла.
    # time_cost: количество итераций (защита от перебора).
    # memory_cost: объем памяти (в KiB), необходимый для вычисления (защита от ASIC/GPU).
    # parallelism: количество параллельных потоков.
    argon2__time_cost=settings.ARGON2_TIME_COST,
    argon2__memory_cost=settings.ARGON2_MEMORY_COST,
    argon2__parallelism=settings.ARGON2_PARALLELISM,
)


def hash_password(password: str) -> str:
    """Хеширует пароль с использованием настроенного алгоритма (Argon2id)."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет, соответствует ли открытый пароль хешированному.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """
    Создает JWT access токен.
    """
    to_encode = data.copy()
    # Получаем текущее время один раз
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Явно устанавливаем ОБА временных поля: 'iat' и 'exp'
    to_encode.update({"iat": int(now.timestamp()), "exp": int(expire.timestamp())})

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
