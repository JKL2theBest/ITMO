from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session
from app.repositories.sqlalchemy.user import UserRepository
from app.services.users import UserService
from app.repositories.sqlalchemy.news import NewsRepository
from app.services.news import NewsService
from app.repositories.sqlalchemy.comment import CommentRepository
from app.services.comments import CommentService

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
