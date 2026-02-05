import uuid
import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    name: str
    email: EmailStr
    avatar_url: str | None = None


class UserCreate(UserBase):
    is_verified_author: bool = False


class UserUpdate(BaseModel):
    name: str | None = None
    avatar_url: str | None = None
    is_verified_author: bool | None = None


class UserResponse(UserBase):
    id: uuid.UUID
    registered_at: datetime.datetime
    is_verified_author: bool

    model_config = ConfigDict(
        from_attributes=True
    )  # Позволяет Pydantic читать данные и из атрибутов объекта (из ORM-модели SQLAlchemy)
