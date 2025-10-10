import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db_session
from app.models.comment import Comment
from app.models.news import News
from app.models.user import User
from app.repositories.sqlalchemy.comment import CommentRepository
from app.repositories.sqlalchemy.news import NewsRepository
from app.repositories.sqlalchemy.user import UserRepository
from app.schemas.role import UserRole
from app.services.comments import CommentService
from app.services.news import NewsService
from app.services.users import UserService

DBSession = Annotated[AsyncSession, Depends(get_db_session)]


# --- РЕПОЗИТОРИИ ---
def get_user_repo(session: DBSession) -> UserRepository:
    return UserRepository(session)


UserRepoDep = Annotated[UserRepository, Depends(get_user_repo)]


def get_news_repo(session: DBSession) -> NewsRepository:
    return NewsRepository(session)


NewsRepoDep = Annotated[NewsRepository, Depends(get_news_repo)]


def get_comment_repo(session: DBSession) -> CommentRepository:
    return CommentRepository(session)


CommentRepoDep = Annotated[CommentRepository, Depends(get_comment_repo)]


# --- СЕРВИСЫ ---
def get_user_service(user_repo: UserRepoDep) -> UserService:
    return UserService(user_repo)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


def get_news_service(news_repo: NewsRepoDep, user_repo: UserRepoDep) -> NewsService:
    return NewsService(news_repo=news_repo, user_repo=user_repo)


NewsServiceDep = Annotated[NewsService, Depends(get_news_service)]


def get_comment_service(
    comment_repo: CommentRepoDep,
    user_repo: UserRepoDep,
    news_repo: NewsRepoDep,
) -> CommentService:
    return CommentService(
        comment_repo=comment_repo,
        user_repo=user_repo,
        news_repo=news_repo,
    )


CommentServiceDep = Annotated[CommentService, Depends(get_comment_service)]

# --- ЗАВИСИМОСТИ АУТЕНТИФИКАЦИИ И АВТОРИЗАЦИИ ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], user_repo: UserRepoDep
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except (JWTError, ValidationError):
        raise credentials_exception

    user = await user_repo.get_by_id(uuid.UUID(user_id))
    if user is None:
        raise credentials_exception
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def require_role(required_roles: list[UserRole]):
    """Фабрика зависимостей для проверки ролей."""

    def role_checker(current_user: CurrentUserDep) -> User:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user does not have enough privileges",
            )
        return current_user

    return role_checker


# --- РЕЗОЛВЕРЫ (ПРОВЕРКА ВЛАДЕНИЯ) ---
async def get_news_for_update(
    news_id: uuid.UUID, current_user: CurrentUserDep, news_repo: NewsRepoDep
) -> News:
    """
    Получает новость по ID и проверяет, имеет ли пользователь
    право на ее изменение (автор или админ).
    """
    news = await news_repo.get_by_id(news_id)
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    if news.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return news


async def get_comment_for_update(
    comment_id: uuid.UUID,
    current_user: CurrentUserDep,
    comment_repo: CommentRepoDep,
) -> Comment:
    """
    Получает комментарий по ID и проверяет, имеет ли пользователь
    право на его изменение (автор или админ).
    """
    comment = await comment_repo.get_by_id(comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this comment",
        )

    return comment


async def get_user_for_update(
    user_id: uuid.UUID, current_user: CurrentUserDep, user_repo: UserRepoDep
) -> User:
    """Проверяет, имеет ли пользователь право на изменение профиля (своего или админ)."""
    user_to_update = await user_repo.get_by_id(user_id)
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found")
    if user_to_update.id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return user_to_update
