import uuid
from typing import List
from fastapi import APIRouter, status
from app.schemas.comment import CommentCreate, CommentResponse, CommentUpdate
from app.api.dependencies import CommentServiceDep, CommentRepoDep

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(comment_data: CommentCreate, service: CommentServiceDep):
    """Создать новый комментарий."""
    return await service.create_comment(comment_data)


@router.get("/", response_model=List[CommentResponse])
async def get_all_comments(
    comment_repo: CommentRepoDep, skip: int = 0, limit: int = 100
):
    """Получить список всех комментариев."""
    return await comment_repo.get_multi(skip=skip, limit=limit)


@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(comment_id: uuid.UUID, service: CommentServiceDep):
    """Получить комментарий по ID."""
    return await service.get_by_id(comment_id)


@router.patch("/{comment_id}", response_model=CommentResponse)
async def update_comment_partial(
    comment_id: uuid.UUID, comment_data: CommentUpdate, service: CommentServiceDep
):
    """Частично обновить текст комментария."""
    return await service.update_comment(comment_id, comment_data)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(comment_id: uuid.UUID, service: CommentServiceDep):
    """Удалить комментарий."""
    await service.delete_comment(comment_id)
