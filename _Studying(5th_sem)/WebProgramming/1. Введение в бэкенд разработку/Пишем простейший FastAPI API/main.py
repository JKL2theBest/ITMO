from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class RegisterRequest(BaseModel):
    username: str
    password: str
    secret: str

class LoginRequest(BaseModel):
    username: str
    password: str

fake_db = {}
current_user = None

@app.get("/")
def root():
    return None

@app.post("/register")
def register(data: RegisterRequest):
    fake_db[data.username] = {"password": data.password, "secret": data.secret}
    return {"message": "registered"}

@app.post("/login")
def login(data: LoginRequest):
    global current_user
    user = fake_db.get(data.username)
    if not user or user["password"] != data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    current_user = data.username
    return {"username": data.username, "password": data.password, "token": "dummy_token"}

@app.get("/me")
def me():
    if not current_user:
        return {"username": None, "secret": None}
    user = fake_db[current_user]
    return {"username": current_user, "secret": user["secret"]}
