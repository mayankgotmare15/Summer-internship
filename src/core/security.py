"""Security, password hashing, JWT session encoding, and service token validation."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from src.app.settings import get_settings

settings = get_settings()

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored password hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Computes secure hash for a plain password."""
    return pwd_context.hash(password)


hash_password = get_password_hash


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Generates an HMAC-signed JWT token with claims."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.jwt_expiration_minutes)

    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodes and validates a JWT token; returns claims payload or raises JWTError."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def verify_service_token(provided_token: str, expected_token: str | None = None) -> bool:
    """Constant-time token verification for internal/CI endpoints."""
    expected = expected_token or settings.service_token
    if not provided_token or not expected:
        return False
    return hmac.compare_digest(provided_token.strip(), expected.strip())


def generate_opaque_token(nbytes: int = 32) -> str:
    """Generates a secure cryptographically random URL-safe token."""
    return secrets.token_urlsafe(nbytes)


def hash_token(token: str) -> str:
    """Computes SHA-256 hex digest of a token string for safe database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

