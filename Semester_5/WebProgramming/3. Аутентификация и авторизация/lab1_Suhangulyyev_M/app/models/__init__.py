from app.db.session import Base
from .user import User
from .news import News
from .comment import Comment
from .refresh_token import RefreshToken

# Для ruff
__all__ = [
    "Base",
    "User",
    "News",
    "Comment",
    "RefreshToken",
]
