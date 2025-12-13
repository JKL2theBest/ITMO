from typing import Generic, Sequence, Type, TypeVar
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Query
from pydantic import BaseModel
from app.db.session import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class SQLAlchemyRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    model: Type[ModelType] = None
    _load_options: Sequence[Query] = []  # Для "жадной" загрузки (Eager loading)

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, obj_id: uuid.UUID) -> ModelType | None:
        """Получает объект по ID с жадной загрузкой."""
        query = select(self.model).where(self.model.id == obj_id)
        if self._load_options:
            query = query.options(*self._load_options)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def create(self, data: CreateSchemaType) -> ModelType:
        """Создает объект и возвращает его с жадно загруженными связями."""
        db_obj = self.model(**data.model_dump())
        self.session.add(db_obj)
        await self.session.commit()
        return await self.get_by_id(db_obj.id)

    async def get_multi(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """Получает список объектов с жадной загрузкой."""
        query = select(self.model).order_by(self.model.id).offset(skip).limit(limit)
        if self._load_options:
            query = query.options(*self._load_options)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update(
        self, db_obj: ModelType, update_data: UpdateSchemaType
    ) -> ModelType:
        """Обновляет объект и возвращает его с жадно загруженными связями."""
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(db_obj, field, value)
        self.session.add(db_obj)
        await self.session.commit()
        return await self.get_by_id(db_obj.id)

    async def delete(self, db_obj: ModelType) -> None:
        """Удаляет объект."""
        await self.session.delete(db_obj)
        await self.session.commit()
