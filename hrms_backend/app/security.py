# security.py
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import os
import hashlib

SECRET = os.getenv("JWT_SECRET", "fallback_secret_key")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

import hashlib

def hash_password(password: str) -> str:
    # ALWAYS convert to SHA256 first
    sha = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return pwd_context.hash(sha)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    sha = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    return pwd_context.verify(sha, hashed_password)

def create_token(data: dict):
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=2)
    return jwt.encode(payload, SECRET, algorithm="HS256")

