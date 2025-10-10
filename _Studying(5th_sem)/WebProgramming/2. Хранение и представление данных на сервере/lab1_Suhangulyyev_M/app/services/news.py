import uuid
from fastapi import HTTPException, status
from app.repositories.sqlalchemy.news import NewsRepository
from app.repositories.sqlalchemy.user import UserRepository
from app.schemas.news import NewsCreate, NewsUpdate
from app.models.news import News
from app.services.base import BaseService


class NewsService(BaseService):
    def __init__(self, news_repo: NewsRepository, user_repo: UserRepository):
        super().__init__(news_repo)
        self.user_repo = user_repo

    async def create_news(self, news_data: NewsCreate) -> News:
        author = await self.user_repo.get_by_id(news_data.author_id)
        if not author:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Author does not exist"
            )

        if not author.is_verified_author:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user is not verified like an author and cannot post news",
            )
        return await self.repository.create(news_data)

    async def update_news(self, news_id: uuid.UUID, news_data: NewsUpdate) -> News:
        news_to_update = await self.get_by_id(news_id)
        return await self.repository.update(
            db_obj=news_to_update, update_data=news_data
        )

    async def delete_news(self, news_id: uuid.UUID) -> None:
        news_to_delete = await self.get_by_id(news_id)
        await self.repository.delete(db_obj=news_to_delete)
