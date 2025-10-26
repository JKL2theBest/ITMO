from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Класс для управления конфигурацией приложения.
    Pydantic автоматически читает переменные из .env файла и системного окружения.
    """

    # --- Application Settings ---
    APP_ENV: str = "development"

    # --- Database Settings ---
    DATABASE_URL: str

    # --- Security & JWT Configuration ---
    # Схема хеширования паролей.
    HASH_SCHEME: str
    # Секретный ключ для подписи JWT токенов.
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"

    # --- Argon2id Parameters ---
    # Эти параметры определяют криптостойкость хеша.
    ARGON2_TIME_COST: int  # итерации
    ARGON2_MEMORY_COST: int  # в кибибайтах
    ARGON2_PARALLELISM: int  # потоки

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
