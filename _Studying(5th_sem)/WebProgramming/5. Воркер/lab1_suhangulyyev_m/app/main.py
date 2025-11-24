from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import users, news, comments, auth
from app.db.cache import init_redis_pool, close_redis_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Действия при старте
    await init_redis_pool()
    yield
    # Действия при остановке
    await close_redis_pool()


app = FastAPI(title="lab1_Suhangulyyev_M", lifespan=lifespan)

# НАСТРОЙКА CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(news.router, prefix="/api/v1")
app.include_router(comments.router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"message": "Welcome to the news API"}
