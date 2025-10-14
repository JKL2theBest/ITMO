from app.models.news import News
from app.models.user import User
from app.repositories.sqlalchemy.news import NewsRepository
from app.schemas.news import NewsCreate, NewsCreateIn, NewsUpdate
from app.services.base import BaseService


class NewsService(BaseService):
    def __init__(self, news_repo: NewsRepository):
        super().__init__(news_repo)

    async def create_news(self, news_data: NewsCreateIn, author: User) -> News:
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
