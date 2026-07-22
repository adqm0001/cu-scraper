from dotenv import load_dotenv
from datetime import datetime, timedelta
from cu_scraper import info
from db import register as db_register, fetch_and_store_grades, get_user, get_grades as db_get_grades, delete_user as db_delete_user, check_changes, update_grades
from db import get_user_credentials, update_email as db_update_email, update_password as db_update_password, verify_user_password
import os
from poller import send_welcome_email, send_goodbye_email, send_grade_change_email, send_email_changed_old, send_email_changed_new
from fastapi import BackgroundTasks, FastAPI, HTTPException, Depends, Request
from jose import jwt
from jose.exceptions import JWTError
from pydantic import BaseModel, Field, EmailStr
import bcrypt
from typing import Annotated
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from datetime import datetime, timedelta, timezone
load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
assert JWT_SECRET, "JWT_SECRET missing"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES") or 60)
TRUSTED_HOSTS = [h.strip() for h in os.getenv("TRUSTED_HOSTS", "").split(",") if h.strip()]
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
security = HTTPBearer()

def get_current_user_id(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]) -> str:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized access")
    return payload["sub"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
if TRUSTED_HOSTS:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=TRUSTED_HOSTS)

class RegisterRequest(BaseModel):
    username: str = Field(max_length=50)
    password: str = Field(max_length=70)
    email: EmailStr = Field(max_length=70)

class UpdateEmailRequest(BaseModel):
    email: EmailStr = Field(max_length=70)
    current_password: str = Field(max_length=70)

class UpdatePasswordRequest(BaseModel):
    password: str = Field(max_length=70)

class DeleteAccountRequest(BaseModel):
    current_password: str = Field(max_length=70)

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
    if user == "username not found":
        raise HTTPException(status_code=401, detail="invalid credentials")
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
async def get_grades(user_id: Annotated[str, Depends(get_current_user_id)]):
    grades, last_updated = await db_get_grades(user_id)

    return {"grades": grades, "last_updated": last_updated}

@app.post("/grades/check")
@limiter.limit("5/minute")
async def check_grades(request: Request, user_id: Annotated[str, Depends(get_current_user_id)]):
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

@app.get("/users/me")
async def get_me(user_id: Annotated[str, Depends(get_current_user_id)]):
    user = await get_user_credentials(user_id)
    if user == "user_id not found":
        raise HTTPException(status_code=404, detail="user not found")

    return {"username": user["username"], "email": user["email"]}

@app.patch("/users/me/email")
@limiter.limit("5/minute")
async def update_email(request: Request, req: UpdateEmailRequest, background_tasks: BackgroundTasks, user_id: Annotated[str, Depends(get_current_user_id)]):
    if not await verify_user_password(user_id, req.current_password):
        raise HTTPException(status_code=401, detail="invalid credentials")

    user = await get_user_credentials(user_id)
    if user == "user_id not found":
        raise HTTPException(status_code=404, detail="user not found")

    old_email = user["email"]
    username = user["username"]
    await db_update_email(user_id, req.email)
    background_tasks.add_task(send_email_changed_old, old_email, username)
    background_tasks.add_task(send_email_changed_new, req.email, username)
    return {"success": True}

@app.patch("/users/me/password")
@limiter.limit("5/minute")
async def update_password(request: Request, req: UpdatePasswordRequest, user_id: Annotated[str, Depends(get_current_user_id)]):
    user = await get_user_credentials(user_id)
    if user == "user_id not found":
        raise HTTPException(status_code=404, detail="user not found")

    result = await info(user["username"], req.password)
    if result is None:
        raise HTTPException(status_code=401, detail="invalid credentials")

    await db_update_password(user_id, req.password)
    return {"success": True}

@app.delete("/users/me")
async def delete_user(req: DeleteAccountRequest, background_tasks: BackgroundTasks, user_id: Annotated[str, Depends(get_current_user_id)]):
    if not await verify_user_password(user_id, req.current_password):
        raise HTTPException(status_code=401, detail="invalid credentials")

    user_creds = await get_user_credentials(user_id)
    if user_creds == "user_id not found":
        raise HTTPException(status_code=404, detail="user not found")
    username = user_creds["username"]
    email = user_creds["email"]
    background_tasks.add_task(send_goodbye_email, email, username)

    await db_delete_user(user_id)

    return {"success": True}


