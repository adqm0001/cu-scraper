from dotenv import load_dotenv
from datetime import datetime, timedelta
from cu_scraper import info
from db import register as db_register, fetch_and_store_grades, get_user, get_grades as db_get_grades, delete_user as db_delete_user, check_changes, update_grades
from db import get_user_credentials
import os
from poller import send_welcome_email, send_goodbye_email, send_grade_change_email
from fastapi import BackgroundTasks, FastAPI, HTTPException, Depends, Request
from jose import jwt
from pydantic import BaseModel, Field
import bcrypt
from typing import Annotated
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from datetime import datetime, timedelta, timezone
load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES") or 60)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class RegisterRequest(BaseModel):
    username: str = Field(max_length=50)
    password: str = Field(max_length=70)
    email: str = Field(max_length=70)

class LoginRequest(BaseModel):
    username: str = Field(max_length=50)
    password: str = Field(max_length=70)

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.post("/register")
@limiter.limit("10/hour")
async def register(request: Request, req: RegisterRequest, background_tasks: BackgroundTasks):
    result = await db_register(req.username, req.password, req.email)
    invalid_msg = "invalid credentials"
    userexists_msg = "username already exists"
    if result == "invalid credentials":
        raise HTTPException(status_code=401, detail=invalid_msg) 
    elif result == userexists_msg:
        raise HTTPException(status_code=409, detail=userexists_msg)
    else:
        user_id, result_info = result
        background_tasks.add_task(fetch_and_store_grades, user_id, result_info)
        background_tasks.add_task(send_welcome_email, req.email, req.username)

        token = jwt.encode(
                {"sub": str(user_id), "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)},
                JWT_SECRET,
                algorithm="HS256"
        )
        return {"accessToken": token}

@app.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, req: LoginRequest):
    user = await get_user(req.username)
    usernotfound_msg = "username not found"

    if user == usernotfound_msg:
        raise HTTPException(status_code=401, detail=usernotfound_msg)
    else:
        if not bcrypt.checkpw(req.password.encode(), user["hashed_password"].encode()):
            raise HTTPException(status_code=401, detail="invalid credentials")
        token = jwt.encode(
                {"sub": str(user["user_id"]), "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)},
                JWT_SECRET,
                algorithm="HS256"
        )
        return {"accessToken": token}

@app.get("/grades")
async def get_grades(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized access")
    user_id = payload["sub"]

    grades, last_updated = await db_get_grades(user_id)

    return {"grades": grades, "last_updated": last_updated}

@app.post("/grades/check")
@limiter.limit("5/minute")
async def check_grades(request: Request, credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=401, detail="Unauthorized access")
    user_id = payload["sub"]

    user_creds = await get_user_credentials(user_id)
    if user_creds == "user_id not found":
        raise HTTPException(status_code=404, detail="user not found")
    result = await info(user_creds["username"], user_creds["password"])
    if result is None:
        return "invalid credentials"

    _,_,_,_, fresh_courses, _ = result 
    changes = await check_changes(user_id, fresh_courses)
    if changes:
        send_grade_change_email(user_creds["email"], changes)
        await update_grades(user_id, changes)

    await fetch_and_store_grades(user_id, result)
    
    return fresh_courses

@app.delete("/users/me")
async def delete_user(background_tasks: BackgroundTasks, credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception as e:
        print(f"JWT error: {e}")
        raise HTTPException(status_code=401, detail="Unauthorized access")
    user_id = payload["sub"]
    user_creds = await get_user_credentials(user_id)
    if user_creds == "user_id not found":
        raise HTTPException(status_code=404, detail="user not found")
    username = user_creds["username"]
    email = user_creds["email"]
    background_tasks.add_task(send_goodbye_email, email, username)

    await db_delete_user(user_id) 

    return {"sucess": True}


