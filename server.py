from dotenv import load_dotenv
from datetime import datetime, timedelta
from cu_scraper import info
from db import register as db_register, fetch_and_store_grades, get_user, get_grades as db_get_grades, delete_user as db_delete_user
from db import get_user_credentials
import os
from poller import send_welcome_email
from fastapi import BackgroundTasks, FastAPI, HTTPException, Depends
from jose import jwt
from pydantic import BaseModel
import bcrypt
from typing import Annotated
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES") or 60)

app = FastAPI()
security = HTTPBearer()

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str

class LoginRequest(BaseModel):
    username: str
    password: str

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.post("/register")
async def register(req: RegisterRequest, background_tasks: BackgroundTasks):
    registration = await db_register(req.username, req.password, req.email)
    invalid_msg = "invalid credentials"
    userexists_msg = "username already exists"

    if registration == invalid_msg:
       raise HTTPException(status_code=401, detail=invalid_msg) 
    elif registration == userexists_msg:
        raise HTTPException(status_code=409, detail=userexists_msg)
    else:
        background_tasks.add_task(fetch_and_store_grades, registration, req.username, req.password)
        background_tasks.add_task(send_welcome_email, req.email, req.username)

        token = jwt.encode(
                {"sub": registration, "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)},
                JWT_SECRET,
                algorithm="HS256"
        )
        return {"accessToken": token}

@app.post("/login")
async def login(req: LoginRequest):
    user = await get_user(req.username)
    usernotfound_msg = "username not found"

    if user == usernotfound_msg:
        raise HTTPException(status_code=401, detail=usernotfound_msg)
    else:
        if not bcrypt.checkpw(req.password.encode(), user["hashed_password"].encode()):
            raise HTTPException(status_code=401, detail="invalid credentials")
        token = jwt.encode(
                {"sub": user["user_id"], "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)},
                JWT_SECRET,
                algorithm="HS256"
        )
        return {"accessToken": token}

@app.get("/grades")
async def get_grades(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except:
        raise HTTPException(status_code=401, detail="Unauthorized access")
    user_id = payload["sub"]

    grades = await db_get_grades(user_id)

    return grades

@app.post("/grades/check")
async def check_grades(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except:
        raise HTTPException(status_code=401, detail="Unauthorized access")
    user_id = payload["sub"]

    user_creds = await get_user_credentials(user_id)
    if user_creds == "user_id not found":
        raise HTTPException(status_code=404, detail="user not found")
    result = await info(user_creds["username"], user_creds["password"])
    if result is None:
        return "invalid credentials"
    _,_,_,_, all_courses = result 
    
    return all_courses

@app.delete("/users/me")
async def delete_user(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except:
        raise HTTPException(status_code=401, detail="Unauthorized access")
    user_id = payload["sub"]

    await db_delete_user(user_id) 

    return {"sucess": True}


