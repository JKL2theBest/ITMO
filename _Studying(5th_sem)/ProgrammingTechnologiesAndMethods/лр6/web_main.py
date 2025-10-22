"""
Точка входа для веб-приложения на FastAPI.
"""

from contextlib import asynccontextmanager
from typing import Annotated, List

from fastapi import FastAPI, Depends, HTTPException, status, Request, Header
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from db.database import AsyncSessionFactory, init_db
from db.models import User
from services.auth_service import AuthService
from services.role_service import RoleService
from services.session_service import SessionService
from schemas.user_schemas import UserCreate, UserPublic


# --- Управление жизненным циклом (Lifespan) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    app.state.session_factory = AsyncSessionFactory
    yield


app = FastAPI(lifespan=lifespan, title="Auth System API")

# --- Раздача статики ---
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")
templates = Jinja2Templates(directory="frontend")


# --- Схемы данных для API ---
class LoginRequest(BaseModel):
    username: str
    password: str
    mfa_code: str | None = None


class TokenResponse(BaseModel):
    session_token: str
    message: str | None = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)


class MFAEnableResponse(BaseModel):
    secret: str
    qr_code_uri: str


# --- Зависимости (Dependencies) ---
async def get_db_session(request: Request) -> AsyncSession:
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        async with session.begin():
            yield session


async def get_auth_service(
    session: AsyncSession = Depends(get_db_session),
) -> AuthService:
    return AuthService(session)


async def get_session_service(
    session: AsyncSession = Depends(get_db_session),
) -> SessionService:
    return SessionService(session)


async def get_role_service(
    session: AsyncSession = Depends(get_db_session),
) -> RoleService:
    return RoleService(session)


# --- ЗАЩИТА ЭНДПОИНТОВ: Зависимость для получения текущего пользователя ---
async def get_current_user(
    token: Annotated[str | None, Header(alias="X-Auth-Token")] = None,
    service: SessionService = Depends(get_session_service),
) -> User:
    """
    Проверяет токен из заголовка X-Auth-Token и возвращает объект User.
    Если токен невалиден или отсутствует, вызывает HTTPException.
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Auth token not provided"
        )
    user = await service.get_user_by_token(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
    return user


# --- Зависимость для проверки роли администратора ---
def require_admin(user: Annotated[User, Depends(get_current_user)]):
    """
    Проверяет, является ли текущий пользователь администратором.
    Используется в Depends для защиты эндпоинтов.
    """
    if user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator rights required",
        )


# --- Эндпоинты (API Routes) ---


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    tags=["Auth"],
)
async def register(
    user_data: UserCreate, service: AuthService = Depends(get_auth_service)
):
    try:
        return await service.register_user(user_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/login", response_model=TokenResponse, tags=["Auth"])
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
    session_service: SessionService = Depends(get_session_service),
):
    try:
        user, mfa_required = await auth_service.authenticate_user(
            request.username, request.password
        )
        if mfa_required:
            if not request.mfa_code:
                # Возвращаем специальный статус, чтобы фронтенд понял, что нужно запросить MFA код
                return JSONResponse(
                    status_code=status.HTTP_202_ACCEPTED,
                    content={"message": "MFA code required"},
                )
            if not user.mfa_secret or not auth_service.mfa_service.verify_code(
                user.mfa_secret, request.mfa_code
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA code"
                )
        new_session = await session_service.create_session(user)
        return TokenResponse(session_token=new_session.token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@app.post("/logout", status_code=status.HTTP_204_NO_CONTENT, tags=["Auth"])
async def logout(
    user: User = Depends(get_current_user),
    service: SessionService = Depends(get_session_service),
    token: str = Header(alias="X-Auth-Token"),
):
    await service.terminate_session(token)


@app.post("/change-password", status_code=status.HTTP_204_NO_CONTENT, tags=["User"])
async def change_password(
    request: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
    token: str = Header(alias="X-Auth-Token"),
):
    try:
        await service.change_password(token, request.old_password, request.new_password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/resources/{resource_name}", tags=["Resources"])
async def get_resource(resource_name: str, user: User = Depends(get_current_user)):
    if resource_name == "admin_resource" and user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    if resource_name not in ["common_resource", "admin_resource"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )
    return {"resource": resource_name, "content": f"Content of {resource_name}"}


# --- Админские эндпоинты ---
@app.get(
    "/admin/roles",
    response_model=List[str],
    dependencies=[Depends(require_admin)],
    tags=["Admin"],
)
async def list_roles(service: RoleService = Depends(get_role_service)):
    return await service.list_roles()


@app.post(
    "/admin/roles/{role_name}",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
    tags=["Admin"],
)
async def create_role(role_name: str, service: RoleService = Depends(get_role_service)):
    try:
        await service.create_role(role_name)
        return {"message": f"Role '{role_name}' created successfully."}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.put(
    "/admin/users/{username}/role",
    response_model=UserPublic,
    dependencies=[Depends(require_admin)],
    tags=["Admin"],
)
async def assign_role(
    username: str, role_name: str, service: RoleService = Depends(get_role_service)
):
    try:
        return await service.assign_role_to_user(username, role_name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.post(
    "/admin/users/{username}/enable-mfa",
    response_model=MFAEnableResponse,
    dependencies=[Depends(require_admin)],
    tags=["Admin"],
)
async def enable_mfa(username: str, service: AuthService = Depends(get_auth_service)):
    user = await service.user_repo.get_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found.",
        )
    if user.is_mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is already enabled."
        )

    secret = service.mfa_service.generate_secret()
    user.mfa_secret = secret
    user.is_mfa_enabled = True
    await service.user_repo.update_user(user)

    uri = service.mfa_service.get_provisioning_uri(username, secret)
    return MFAEnableResponse(
        secret=secret,
        qr_code_uri=f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={uri}",
    )
