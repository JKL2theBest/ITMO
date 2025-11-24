import uuid
from typing import List, Annotated
from fastapi import APIRouter, status, Depends
from app.schemas.comment import CommentCreateIn, CommentResponse, CommentUpdate
from app.models.comment import Comment
from app.api.dependencies import (
    CommentServiceDep,
    CommentRepoDep,
    CurrentUserDep,
    get_comment_for_update,
)

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_data: CommentCreateIn,
    service: CommentServiceDep,
    current_user: CurrentUserDep,
):
    """Создать новый комментарий (любой авторизованный пользователь)."""
    return await service.create_comment(comment_data, author=current_user)


@router.get("/", response_model=List[CommentResponse])
async def get_all_comments(
    comment_repo: CommentRepoDep,
    current_user: CurrentUserDep,
    skip: int = 0,
    limit: int = 100,
):
    """Получить список всех комментариев."""
    return await comment_repo.get_multi(skip=skip, limit=limit)


@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: uuid.UUID, service: CommentServiceDep, current_user: CurrentUserDep
):
    """Получить комментарий по ID."""
    return await service.get_by_id(comment_id)


@router.patch("/{comment_id}", response_model=CommentResponse)
async def update_comment_partial(
    comment_data: CommentUpdate,
    service: CommentServiceDep,
    comment_to_update: Annotated[Comment, Depends(get_comment_for_update)],
):
    """Частично обновить комментарий (автор или админ)."""
    return await service.update_comment(comment_to_update, comment_data)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    service: CommentServiceDep,
    comment_to_delete: Annotated[Comment, Depends(get_comment_for_update)],
):
    """Удалить комментарий (автор или админ)."""
    await service.delete_comment(comment_to_delete)
