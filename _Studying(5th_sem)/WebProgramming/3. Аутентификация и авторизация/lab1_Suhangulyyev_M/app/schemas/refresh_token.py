import datetime
from pydantic import BaseModel, ConfigDict


class RefreshTokenResponse(BaseModel):
    id: int
    user_agent: str | None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
