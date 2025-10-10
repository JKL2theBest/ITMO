import uuid
from fastapi import HTTPException, status


class BaseService:
    def __init__(self, repository):
        self.repository = repository

    async def get_by_id(self, obj_id: uuid.UUID):
        db_obj = await self.repository.get_by_id(obj_id)
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.repository.model.__name__} not found",
            )
        return db_obj
