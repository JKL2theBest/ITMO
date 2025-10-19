import uuid
from typing import List, Annotated
from fastapi import APIRouter, status, Depends, HTTPException
from app.schemas.news import NewsCreateIn, NewsResponse, NewsUpdate
from app.models.news import News
from app.api.dependencies import (
    NewsServiceDep,
    NewsRepoDep,
    CurrentUserDep,
    get_news_for_update,
    require_role,
)
from app.schemas.role import UserRole
from app.models.user import User

router = APIRouter(prefix="/news", tags=["news"])


@router.post("/", response_model=NewsResponse, status_code=status.HTTP_201_CREATED)
async def create_news(
    news_data: NewsCreateIn,
    service: NewsServiceDep,
    current_user: Annotated[
        User, Depends(require_role([UserRole.ADMIN, UserRole.VERIFIED_AUTHOR]))
    ],
):
    """Создать новость (только верифицированный автор или админ)."""
    return await service.create_news(news_data, current_user)


@router.get("/", response_model=List[NewsResponse])
async def get_all_news(
    news_repo: NewsRepoDep,
    current_user: CurrentUserDep,
    skip: int = 0,
    limit: int = 100,
):
    """Получить список всех новостей."""
    return await news_repo.get_multi(skip=skip, limit=limit)


@router.get("/{news_id}", response_model=NewsResponse)
async def get_news(
    news_id: uuid.UUID, service: NewsServiceDep, current_user: CurrentUserDep
):
    """Получить одну новость по ID."""
    news = await service.get_by_id(news_id)
    # Сервис уже сам выбрасывает 404, но проверка для надежности не помешает
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    return news


@router.patch("/{news_id}", response_model=NewsResponse)
async def update_news_partial(
    news_update_data: NewsUpdate,
    service: NewsServiceDep,
    news_to_update: Annotated[News, Depends(get_news_for_update)],
):
    """Частично обновить новость (автор или админ)."""
    return await service.update_news(news_to_update, news_update_data)


@router.delete("/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_news(
    service: NewsServiceDep,
    news_to_delete: Annotated[News, Depends(get_news_for_update)],
):
    """Удалить новость (автор или админ)."""
    await service.delete_news(news_to_delete)
