from fastapi import FastAPI
from app.api.v1 import users, news, comments

app = FastAPI(title="lab1_Suhangulyyev_M")

app.include_router(users.router, prefix="/api/v1")
app.include_router(news.router, prefix="/api/v1")
app.include_router(comments.router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"message": "Welcome to the news API"}
