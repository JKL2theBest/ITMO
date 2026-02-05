import uuid
from fastapi import HTTPException, status
from app.repositories.sqlalchemy.comment import CommentRepository
from app.repositories.sqlalchemy.user import UserRepository
from app.repositories.sqlalchemy.news import NewsRepository
from app.schemas.comment import CommentCreate, CommentUpdate
from app.models.comment import Comment
from app.services.base import BaseService


class CommentService(BaseService):
    def __init__(
        self,
        comment_repo: CommentRepository,
        user_repo: UserRepository,
        news_repo: NewsRepository,
    ):
        super().__init__(comment_repo)
        self.user_repo = user_repo
        self.news_repo = news_repo

    async def create_comment(self, comment_data: CommentCreate) -> Comment:
        if not await self.user_repo.get_by_id(comment_data.author_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Comment author not found"
            )

        if not await self.news_repo.get_by_id(comment_data.news_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="News for commenting not found",
            )
        return await self.repository.create(comment_data)

    async def update_comment(
        self, comment_id: uuid.UUID, comment_data: CommentUpdate
    ) -> Comment:
        comment_to_update = await self.get_by_id(comment_id)
        return await self.repository.update(
            db_obj=comment_to_update, update_data=comment_data
        )

    async def delete_comment(self, comment_id: uuid.UUID) -> None:
        comment_to_delete = await self.get_by_id(comment_id)
        await self.repository.delete(db_obj=comment_to_delete)
