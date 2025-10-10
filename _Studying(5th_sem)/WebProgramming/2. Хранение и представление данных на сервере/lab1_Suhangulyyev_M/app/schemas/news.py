import uuid
import datetime
from pydantic import BaseModel, ConfigDict
from .user import UserResponse


class NewsBase(BaseModel):
    title: str
    content: dict  # JSON
    cover_image_url: str | None = None


class NewsCreate(NewsBase):
    author_id: uuid.UUID


class NewsUpdate(BaseModel):
    title: str | None = None
    content: dict | None = None
    cover_image_url: str | None = None


class NewsResponse(NewsBase):
    id: uuid.UUID
    published_at: datetime.datetime
    author: UserResponse

    model_config = ConfigDict(from_attributes=True)
