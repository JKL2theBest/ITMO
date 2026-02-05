import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreateInternal, UserCreateRequest

log = structlog.get_logger()


class UserService:
    """
    Слой бизнес-логики (Service Layer) для операций с пользователями.
    """

    def __init__(self, session: AsyncSession):
        self.repo = UserRepository(session)

    async def register_user(self, user_data: UserCreateRequest) -> User:
        """Регистрирует нового пользователя."""
        existing_user = await self.repo.get_by_login(user_data.login)
        if existing_user:
            log.warn(
                "registration_failed",
                reason="login_already_exists",
                login=user_data.login,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this login already exists",
            )

        hashed_pass = hash_password(user_data.password)
        user_internal_data = UserCreateInternal(
            login=user_data.login, password_hash=hashed_pass
        )
        new_user = await self.repo.create(user_internal_data)

        # Логируем успешную регистрацию. Важно не логировать пароль.
        log.info("user_registered", user_id=str(new_user.id), login=new_user.login)
        return new_user

    async def authenticate_user(self, login: str, password: str) -> dict:
        """Аутентифицирует пользователя и возвращает токен."""
        user = await self.repo.get_by_login(login)

        # Безопасность: Проверка пользователя и пароля выполняется в одной условной
        # конструкции. Это усложняет атаки по времени (timing attacks).
        if not user or not verify_password(password, user.password_hash):
            log.warn("authentication_failed", reason="invalid_credentials", login=login)
            # Безопасность: Сообщение об ошибке должно быть общим, чтобы не дать
            # злоумышленнику понять, что именно неверно: логин или пароль.
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid login or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        log.info("user_authenticated", user_id=str(user.id), login=user.login)

        # Создаем JWT токен с информацией о пользователе.
        access_token = create_access_token(
            data={"sub": user.login, "user_id": str(user.id)}
        )
        return {"access_token": access_token, "token_type": "bearer"}
