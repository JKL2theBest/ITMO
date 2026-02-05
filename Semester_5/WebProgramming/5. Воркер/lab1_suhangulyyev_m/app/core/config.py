from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_ECHO_LOG: bool = True

    DATABASE_URL: str
    SYNC_DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_CALLBACK_URL: str
    REFRESH_TOKEN_EXPIRE_DAYS: int

    REDIS_HOST: str
    REDIS_PORT: int

    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
