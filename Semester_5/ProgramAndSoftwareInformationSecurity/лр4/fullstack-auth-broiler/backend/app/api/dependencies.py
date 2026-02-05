from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.services.user_service import UserService

# Создаем типизированную зависимость для сессии базы данных.
DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]


def get_user_service(db_session: DBSessionDep) -> UserService:
    """
    Фабрика-зависимость для получения экземпляра UserService.
    """
    return UserService(db_session)


# Создаем типизированную зависимость для UserService.
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
