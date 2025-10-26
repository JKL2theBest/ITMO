from fastapi import APIRouter, status

from app.api.dependencies import UserServiceDep
from app.schemas.user import (
    TokenResponse,
    UserCreateRequest,
    UserLoginRequest,
    UserPublic,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
    description="Создает нового пользователя с уникальным логином и паролем, "
    "если логин еще не занят.",
)
async def register_user(
    user_data: UserCreateRequest,
    user_service: UserServiceDep,
) -> UserPublic:
    """
    Обрабатывает запрос на регистрацию нового пользователя.
    """
    new_user = await user_service.register_user(user_data)
    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Аутентификация пользователя",
    description="Проверяет учетные данные и в случае успеха возвращает JWT токен.",
)
async def login_user(
    user_data: UserLoginRequest,
    user_service: UserServiceDep,
) -> TokenResponse:
    """
    Обрабатывает запрос на аутентификацию пользователя.
    """
    token_data = await user_service.authenticate_user(
        user_data.login, user_data.password
    )
    return token_data
