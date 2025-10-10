from fastapi import HTTPException, status
from app.repositories.sqlalchemy.news import NewsRepository
from app.repositories.sqlalchemy.user import UserRepository

from app.schemas.news import NewsCreate, NewsCreateIn, NewsUpdate
from app.models.user import User
from app.models.news import News
from app.schemas.role import UserRole
from app.services.base import BaseService


class NewsService(BaseService):
    def __init__(self, news_repo: NewsRepository, user_repo: UserRepository):
        super().__init__(news_repo)
        self.user_repo = user_repo

    async def create_news(self, news_data: NewsCreateIn, author: User) -> News:
        if author.role not in [UserRole.ADMIN, UserRole.VERIFIED_AUTHOR]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins or verified authors can post news",
            )

        news_dict = news_data.model_dump()
        news_dict["author_id"] = author.id
        final_news_data = NewsCreate(**news_dict)

        return await self.repository.create(final_news_data)

    async def update_news(self, news_to_update: News, news_data: NewsUpdate) -> News:
        return await self.repository.update(
            db_obj=news_to_update, update_data=news_data
        )

    async def delete_news(self, news_to_delete: News) -> None:
        await self.repository.delete(db_obj=news_to_delete)
