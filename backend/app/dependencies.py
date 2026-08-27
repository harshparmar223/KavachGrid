"""
KAVACHGRID 3.0 — Shared Dependencies
Phase 5: Complete — Authentication & API key dependencies

Provides FastAPI dependencies for:
    - Database sessions (get_db)
    - JWT authentication (get_current_user)
    - API key validation (verify_api_key_header)
    - Role-based access control (require_role)
"""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db  # noqa: F401 — re-export for convenience
from app.db.models import User
from app.utils.security import decode_access_token

# ============================================
# OAuth2 scheme for JWT bearer tokens
# ============================================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# ============================================
# API Key header scheme
# ============================================
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# ============================================
# Dependency: Get current authenticated user
# ============================================
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decode a JWT token and return the authenticated User model.

    Raises 401 if token is invalid, expired, or user is inactive/missing.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)
    except (ValueError, AttributeError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    return user


# ============================================
# Dependency: Verify API key header
# ============================================
async def verify_api_key_header(
    api_key: str = Depends(api_key_header),
) -> str:
    """
    Validate the X-API-Key header against the configured API key.

    Used for machine-to-machine endpoints (telemetry ingestion, engine outputs).
    Raises 403 if the key is missing or invalid.
    """
    if not api_key or api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key",
        )
    return api_key


# ============================================
# Factory: Role-based access guard
# ============================================
def require_role(*allowed_roles: str):
    """
    Return a FastAPI dependency that restricts access to specific user roles.

    Usage:
        @router.post("/admin-only", dependencies=[Depends(require_role("admin"))])
        def admin_endpoint(...): ...

        @router.put("/ops", dependencies=[Depends(require_role("admin", "operator"))])
        def ops_endpoint(...): ...
    """

    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' does not have access. "
                       f"Required: {', '.join(allowed_roles)}",
            )
        return current_user

    return role_checker
