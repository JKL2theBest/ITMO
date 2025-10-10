from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SYNC_DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_CALLBACK_URL: str
    REFRESH_TOKEN_EXPIRE_DAYS: int

    TEST_DATABASE_URL: str
    SYNC_TEST_DATABASE_URL: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
