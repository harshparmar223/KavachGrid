"""
KAVACHGRID 3.0 — Security Utilities
Phase 5: Complete Implementation

Provides:
    - Password hashing and verification (bcrypt 5.x direct API)
    - JWT access token creation and decoding (HS256 via python-jose)
    - API key validation against settings
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from app.config import settings

# ============================================
# Password Hashing (bcrypt directly)
# ============================================


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ============================================
# JWT Token Management
# ============================================
def create_access_token(
    subject: UUID,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        subject: User UUID to encode as the 'sub' claim.
        role: User role to encode into the token payload.
        expires_delta: Custom expiration. Defaults to ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Encoded JWT string.
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "sub": str(subject),
        "role": role,
        "exp": expire,
        "iat": now,
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT access token.

    Returns:
        Decoded payload dict with 'sub', 'role', 'exp' keys, or None if invalid.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None


# ============================================
# API Key Validation
# ============================================
def verify_api_key(api_key: str) -> bool:
    """Check whether the provided API key matches the configured key."""
    return api_key == settings.API_KEY
