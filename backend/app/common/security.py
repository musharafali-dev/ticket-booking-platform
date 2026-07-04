"""
Password hashing and JWT token utilities.

Bcrypt is used over faster hashes (e.g. plain SHA-256) deliberately —
it's slow by design, which is exactly what you want for password storage
since it makes brute-force and rainbow-table attacks computationally
expensive even if the hash database leaks.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "role": role, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token_value() -> str:
    """
    Raw refresh token returned to the client. Only its hash is stored server-side
    (see app.auth.models.RefreshToken) so a leaked database dump doesn't hand
    an attacker valid refresh tokens directly.
    """
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """One-way hash for storing refresh/verification tokens at rest."""
    return pwd_context.hash(token)


def verify_token_hash(token: str, token_hash: str) -> bool:
    return pwd_context.verify(token, token_hash)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def generate_verification_token() -> str:
    return secrets.token_urlsafe(32)
