import time
import structlog
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import multiprocess, CollectorRegistry, make_asgi_app
from prometheus_fastapi_instrumentator import Instrumentator
from hawk_python_sdk import Hawk

from app.api.v1 import users, news, comments, auth
from app.db.cache import init_redis_pool, close_redis_pool
from app.core.config import settings
from app.core.logger import configure_logger

# --- ОБЩАЯ НАСТРОЙКА ---
configure_logger()
logger = structlog.get_logger()
hawk_client = None


# --- LIFESPAN ДЛЯ STARTUP/SHUTDOWN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global hawk_client
    # Действия при старте
    prometheus_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
    if prometheus_dir and not os.path.exists(prometheus_dir):
        os.makedirs(prometheus_dir, exist_ok=True)

    # Инициализация Hawk
    if settings.HAWK_TOKEN and settings.HAWK_TOKEN != "your_hawk_token_here":
        print("DEBUG: Initializing Hawk...")
        try:
            hawk_client = Hawk(settings.HAWK_TOKEN)
            print("DEBUG: Hawk client initialized successfully!")
        except Exception as e:
            print(f"ERROR: Failed to initialize Hawk: {e}")
            hawk_client = None

    await init_redis_pool()
    yield
    # Действия при остановке
    await close_redis_pool()


app = FastAPI(title="lab1_Suhangulyyev_M", lifespan=lifespan)


# --- MIDDLEWARES ---


# Middleware для Hawk
@app.middleware("http")
async def hawk_exception_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        if hawk_client:
            print(f"DEBUG: Sending error to Hawk: {e}")
            try:
                hawk_client.send(e)
                print("DEBUG: Error sent to Hawk.")
            except Exception as hawk_e:
                print(f"ERROR: Failed to send to Hawk: {hawk_e}")
        raise e


# Middleware для Structlog
@app.middleware("http")
async def structlog_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", "unknown")
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host if request.client else "unknown",
    )

    start_time = time.perf_counter_ns()

    try:
        response = await call_next(request)
        process_time = time.perf_counter_ns() - start_time

        structlog.contextvars.bind_contextvars(
            status_code=response.status_code,
            process_time=process_time / 10**6,  # ms
        )

        if 400 <= response.status_code < 500:
            logger.warning("Client error")
        elif response.status_code >= 500:
            logger.error("Server error")
        else:
            logger.info("Request processed")

        return response
    except Exception as e:
        # Эта ошибка уже будет поймана middleware для Hawk выше
        logger.exception("Request failed", error=str(e))
        raise e


# Middleware для CORS
origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- PROMETHEUS METRICS ---
Instrumentator().instrument(app)
registry = CollectorRegistry()
multiprocess.MultiProcessCollector(registry)
metrics_app = make_asgi_app(registry=registry)
app.mount("/metrics", metrics_app)


# --- ROUTERS ---
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(news.router, prefix="/api/v1")
app.include_router(comments.router, prefix="/api/v1")


# --- ТЕСТОВЫЕ РУЧКИ ---
@app.get("/")
def read_root():
    logger.info("Root endpoint called")
    return {"message": "Welcome to the news API"}


@app.get("/error_test")
def trigger_error():
    """Тестовая ручка для проверки Hawk"""
    raise ValueError("This is a test error for Hawk!")
