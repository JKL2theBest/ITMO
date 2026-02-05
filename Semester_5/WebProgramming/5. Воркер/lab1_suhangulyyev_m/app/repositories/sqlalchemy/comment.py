from sqlalchemy.orm import selectinload
from app.models.comment import Comment
from app.repositories.sqlalchemy.base import SQLAlchemyRepository
from app.schemas.comment import CommentCreate, CommentUpdate


class CommentRepository(SQLAlchemyRepository[Comment, CommentCreate, CommentUpdate]):
    model = Comment
    _load_options = [
        selectinload(model.author),
        selectinload(model.news),
    ]
