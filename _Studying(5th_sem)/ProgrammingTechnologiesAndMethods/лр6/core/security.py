"""
Модуль обеспечения безопасности.

Содержит функции для хеширования и проверки паролей, а также для
генерации криптографически стойких токенов.
"""

import secrets
from passlib.context import CryptContext

from core.config import settings

# 1. Создание контекста для хеширования паролей.
# Контекст настраивается один раз при запуске приложения.
pwd_context = CryptContext(
    schemes=[settings.PASSWORD_HASH_SCHEME],
    deprecated="auto",
    # 2. Передача параметров Argon2 из конфигурации.
    # Это позволяет гибко настраивать криптостойкость без изменения кода.
    argon2__time_cost=settings.ARGON2_TIME_COST,
    argon2__memory_cost=settings.ARGON2_MEMORY_COST,
    argon2__parallelism=settings.ARGON2_PARALLELISM,
)


def hash_password(password: str) -> str:
    """
    Хеширует предоставленный пароль с использованием Argon2.

    Функция автоматически генерирует уникальную соль для каждого пароля,
    что является критически важной мерой защиты от атак по радужным таблицам.

    Args:
        password: Пароль в открытом виде.

    Returns:
        Строка, содержащая полный хеш, включая алгоритм, параметры,
        соль и сам хеш. Формат пригоден для прямого сохранения в БД.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет, соответствует ли пароль в открытом виде его хешу.

    Использует информацию о соли и параметрах, сохраненную в строке
    хеша, для корректного сравнения.

    Args:
        plain_password: Пароль в открытом виде для проверки.
        hashed_password: Хеш из базы данных для сравнения.

    Returns:
        True, если пароли совпадают, иначе False.
    """
    return pwd_context.verify(plain_password, hashed_password)


def generate_session_token() -> str:
    """
    Генерирует криптографически стойкий токен для сессии.

    Использует модуль `secrets` для генерации безопасного случайного токена,
    который невозможно предсказать.

    Returns:
        Безопасный токен в виде шестнадцатеричной строки.
    """
    return secrets.token_hex(32)  # 64 символа в hex-представлении
