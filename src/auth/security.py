"""
Cryptographic security module providing password hashing, verification,
and HMAC-SHA256 signed access token issuance and verification.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "mlops-secure-enterprise-jwt-token-secret-2026")
TOKEN_EXPIRY_HOURS = 24
PBKDF2_ITERATIONS = 100_000


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """
    Hashes a password using PBKDF2-HMAC-SHA256 with 100,000 iterations.
    Returns (hashed_password_hex, salt_hex).
    """
    if not salt:
        salt = secrets.token_hex(16)

    salt_bytes = salt.encode("utf-8")
    pw_bytes = password.encode("utf-8")

    derived_key = hashlib.pbkdf2_hmac("sha256", pw_bytes, salt_bytes, PBKDF2_ITERATIONS, dklen=32)
    return derived_key.hex(), salt


def verify_password(plain_password: str, hashed_password: str, salt: str) -> bool:
    """
    Verifies a plain password against the stored PBKDF2 hash using constant-time comparison.
    """
    computed_hash, _ = hash_password(plain_password, salt=salt)
    return hmac.compare_digest(computed_hash, hashed_password)


def create_access_token(
    user_id: str,
    role: str,
    department: str,
    name: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Creates an HMAC-SHA256 cryptographically signed session token.
    Token format: base64url(payload).base64url(signature)
    """
    now = datetime.now(timezone.utc)
    expiry = now + (expires_delta or timedelta(hours=TOKEN_EXPIRY_HOURS))

    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "department": department,
        "name": name,
        "iat": int(now.timestamp()),
        "exp": int(expiry.timestamp()),
    }

    payload_json = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_json).decode("utf-8").rstrip("=")

    signature = hmac.new(
        SECRET_KEY.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")

    return f"{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> dict[str, Any] | None:
    """
    Decodes and validates the signature and expiration of an access token.
    Returns payload dictionary or None if invalid or expired.
    """
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None

        payload_b64, sig_b64 = parts

        # Verify signature
        expected_sig = hmac.new(
            SECRET_KEY.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256
        ).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode("utf-8").rstrip("=")

        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            return None

        # Add back base64 padding
        padding = "=" * ((4 - len(payload_b64) % 4) % 4)
        payload_json = base64.urlsafe_b64decode(payload_b64 + padding).decode("utf-8")
        payload = json.loads(payload_json)

        # Verify expiration
        exp = payload.get("exp")
        if not exp or datetime.now(timezone.utc).timestamp() > exp:
            return None

        return payload
    except Exception:
        return None
