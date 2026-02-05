"""
Модуль бизнес-логики для многофакторной аутентификации (MFA/TOTP).
"""

import pyotp


class MFAService:
    """Сервис для управления Time-Based One-Time Password (TOTP)."""

    def generate_secret(self) -> str:
        """Генерирует новый секретный ключ для TOTP (в формате base32)."""
        return pyotp.random_base32()

    def get_provisioning_uri(self, username: str, secret: str) -> str:
        """
        Создает URI для provisioning'а (настройки) в приложении-аутентификаторе.
        Этот URI обычно используется для генерации QR-кода.

        Args:
            username: Имя пользователя, которое будет отображаться в приложении.
            secret: Сгенерированный секретный ключ.

        Returns:
            Строка URI.
        """
        # issuer_name - название вашего сервиса
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=username, issuer_name="AuthSystemLab"
        )

    def verify_code(self, secret: str, code: str) -> bool:
        """
        Проверяет предоставленный одноразовый код.

        Args:
            secret: Секретный ключ пользователя.
            code: Код, введенный пользователем.

        Returns:
            True, если код верный, иначе False.
        """
        totp = pyotp.totp.TOTP(secret)
        return totp.verify(code)
