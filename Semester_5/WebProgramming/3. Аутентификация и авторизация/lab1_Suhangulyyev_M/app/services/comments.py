from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.models.comment import Comment
from app.models.user import User
from app.repositories.sqlalchemy.comment import CommentRepository
from app.schemas.comment import CommentCreate, CommentCreateIn, CommentUpdate
from app.services.base import BaseService


class CommentService(BaseService):
    def __init__(self, comment_repo: CommentRepository):
        super().__init__(comment_repo)

    async def create_comment(
        self, comment_data: CommentCreateIn, author: User
    ) -> Comment:
        internal_comment_dict = comment_data.model_dump()
        internal_comment_dict["author_id"] = author.id

        final_comment_data = CommentCreate(**internal_comment_dict)

        try:
            new_comment = await self.repository.create(final_comment_data)
            return new_comment
        except IntegrityError as e:
            error_info = str(e.orig)
            if "comments_news_id_fkey" in error_info:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"News with id {comment_data.news_id} not found.",
                )
            # Ошибка автора теоретически невозможна, т.к. он берется из токена
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Database integrity error: {error_info}",
            )

    async def update_comment(
        self, comment_to_update: Comment, comment_data: CommentUpdate
    ) -> Comment:
        return await self.repository.update(
            db_obj=comment_to_update, update_data=comment_data
        )

    async def delete_comment(self, comment_to_delete: Comment) -> None:
        await self.repository.delete(db_obj=comment_to_delete)
