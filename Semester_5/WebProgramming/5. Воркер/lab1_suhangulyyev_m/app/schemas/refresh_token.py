import datetime
from pydantic import BaseModel


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponseFromCache(BaseModel):
    refresh_token: str
    user_agent: str | None
    created_at: datetime.datetime | str  # В Redis хранится как ISO-строка
