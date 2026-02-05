from fastapi import FastAPI

from app.api.v1_router import api_v1_router
from app.core.config import settings

# Безопасность: Отключаем Swagger и ReDoc в production-окружении.
docs_url = "/docs" if settings.APP_ENV == "development" else None
redoc_url = "/redoc" if settings.APP_ENV == "development" else None

app = FastAPI(
    title="Lab API",
    description="API для лабораторной работы по Программно-аппаратным средствам защиты информации.",
    version="1.0.0",
    docs_url=docs_url,
    redoc_url=redoc_url,
)

app.include_router(api_v1_router)


@app.get("/", tags=["Health Check"])
def health_check():
    """
    Эндпоинт для проверки работоспособности сервиса (Health Check).
    """
    return {"status": "ok", "environment": settings.APP_ENV}
