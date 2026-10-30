import hashlib
import hmac
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from jose import jwt
from jose.exceptions import JWTError

load_dotenv()

UNSUBSCRIBE_PURPOSE = "unsubscribe_grades"
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://cu-scraper.vercel.app").rstrip("/")


def _unsubscribe_key() -> str:
    secret = os.getenv("JWT_SECRET")
    assert secret, "JWT_SECRET missing"
    return hmac.new(secret.encode(), b"cu-scraper:unsubscribe-grades:v1", hashlib.sha256).hexdigest()


def create_unsubscribe_token(user_id) -> str:
    claims = {
        "sub": str(user_id),
        "purpose": UNSUBSCRIBE_PURPOSE,
        "iat": int(datetime.now(timezone.utc).timestamp()),
    }
    return jwt.encode(claims, _unsubscribe_key(), algorithm="HS256")


def read_unsubscribe_token(token: str) -> str | None:
    try:
        claims = jwt.decode(token, _unsubscribe_key(), algorithms=["HS256"])
    except JWTError:
        return None
    if claims.get("purpose") != UNSUBSCRIBE_PURPOSE or not claims.get("sub"):
        return None
    return claims["sub"]


def unsubscribe_url(user_id) -> str:
    return f"{FRONTEND_URL}/unsubscribe?token={create_unsubscribe_token(user_id)}"
