from fastapi import APIRouter

from app.api.routers import auth

api_v1_router = APIRouter(prefix="/api/v1", tags=["v1"])

api_v1_router.include_router(auth.router, prefix="/auth")
