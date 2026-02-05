from sqlalchemy.orm import selectinload
from app.models.news import News
from app.repositories.sqlalchemy.base import SQLAlchemyRepository
from app.schemas.news import NewsCreate, NewsUpdate


class NewsRepository(SQLAlchemyRepository[News, NewsCreate, NewsUpdate]):
    model = News
    _load_options = [selectinload(model.author)]
