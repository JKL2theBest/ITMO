from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

# Middleware для добавления заголовков безопасности
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    # Разрешаем ресурсы только с текущего домена
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    # HTTPS минимум на год, все поддомены, включение в предзагрузку
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    return response

@app.get("/ping")
def ping():
    return {"message": "Hello, Secure World"}
