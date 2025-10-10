import uuid
from typing import List
from fastapi import APIRouter, status
from app.schemas.news import NewsCreate, NewsResponse, NewsUpdate
from app.api.dependencies import NewsServiceDep, NewsRepoDep

router = APIRouter(prefix="/news", tags=["news"])


@router.post("/", response_model=NewsResponse, status_code=status.HTTP_201_CREATED)
async def create_news(news_data: NewsCreate, service: NewsServiceDep):
    """Создать новость."""
    return await service.create_news(news_data)


@router.get("/", response_model=List[NewsResponse])
async def get_all_news(news_repo: NewsRepoDep, skip: int = 0, limit: int = 100):
    """Получить список всех новостей."""
    return await news_repo.get_multi(skip=skip, limit=limit)


@router.get("/{news_id}", response_model=NewsResponse)
async def get_news(news_id: uuid.UUID, service: NewsServiceDep):
    """Получить одну новость по ID."""
    return await service.get_by_id(news_id)


@router.patch("/{news_id}", response_model=NewsResponse)
async def update_news_partial(
    news_id: uuid.UUID, news_update_data: NewsUpdate, service: NewsServiceDep
):
    """Частично обновить текст новости."""
    return await service.update_news(news_id, news_update_data)


@router.delete("/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_news(news_id: uuid.UUID, service: NewsServiceDep):
    """Удалить новость."""
    await service.delete_news(news_id)
