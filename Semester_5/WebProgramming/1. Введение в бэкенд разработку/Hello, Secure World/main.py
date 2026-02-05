from fastapi import FastAPI, Request

app = FastAPI()


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers["Content-Security-Policy"] = "default-src 'self'"  # CSP

    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains; preload"  # HSTS
    )

    return response


@app.get("/ping")
async def ping():
    # FastAPI сам преобразует в JSONResponse
    return {"message": "Hello, Secure World"}
