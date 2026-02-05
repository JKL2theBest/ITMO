import uuid
from typing import List
from fastapi import APIRouter, status
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.api.dependencies import UserServiceDep, UserRepoDep

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, service: UserServiceDep):
    """Создать нового пользователя."""
    return await service.create_user(user_data)


@router.get("/", response_model=List[UserResponse])
async def get_all_users(
    user_repo: UserRepoDep,
    skip: int = 0,
    limit: int = 100,
):
    """Получить список всех пользователей."""
    return await user_repo.get_multi(skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: uuid.UUID, service: UserServiceDep):
    return await service.get_by_id(user_id)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user_partial(
    user_id: uuid.UUID, user_data: UserUpdate, service: UserServiceDep
):
    """Частично обновить данные пользователя."""
    return await service.update_user(user_id, user_data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: uuid.UUID, service: UserServiceDep):
    """Удалить пользователя."""
    await service.delete_user(user_id)
