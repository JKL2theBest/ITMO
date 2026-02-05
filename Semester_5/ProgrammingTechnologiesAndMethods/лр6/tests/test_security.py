"""
Модульные тесты для модуля core.security.
"""

from core.security import hash_password, verify_password


def test_hash_password_creates_valid_hash():
    """
    Тест 1: Проверяет, что функция хеширования создает непустую строку.
    """
    password = "securepassword123"
    hashed = hash_password(password)
    assert hashed is not None
    assert isinstance(hashed, str)
    assert hashed != password


def test_verify_password_correct():
    """
    Тест 2: Проверяет, что функция верификации правильно определяет верный пароль.
    """
    password = "myverystrongpassword!"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True


def test_verify_password_incorrect():
    """
    Тест 3: Проверяет, что функция верификации правильно определяет неверный пароль.
    """
    password = "myverystrongpassword!"
    wrong_password = "wrongpassword"
    hashed = hash_password(password)
    assert verify_password(wrong_password, hashed) is False


def test_hashes_are_unique_due_to_salt():
    """
    Тест 4: Проверяет, что для одного и того же пароля генерируются разные хеши
            (из-за использования уникальной соли).
    """
    password = "samesamepassword"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    assert hash1 != hash2
    # При этом оба хеша должны быть валидны для одного и того же пароля
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True
