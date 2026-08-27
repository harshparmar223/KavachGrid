"""
KAVACHGRID 3.0 — Auth API
Phase 5: Authentication endpoints

Endpoints:
    POST /auth/login       — Authenticate and receive JWT token
    POST /auth/register    — Create a new user (admin only)
    GET  /auth/me          — Get current user profile
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, require_role
from app.db.models import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import auth_service
from app.utils.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=Token,
    summary="Login and get JWT token",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Authenticate with username and password.
    Returns a JWT access token on success.
    """
    user = auth_service.authenticate_user(
        db, form_data.username, form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    # Update last login timestamp
    auth_service.update_last_login(db, user.id)

    # Generate JWT token
    access_token = create_access_token(subject=user.id, role=user.role)

    return Token(access_token=access_token, token_type="bearer")


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user (admin only)",
    dependencies=[Depends(require_role("admin"))],
)
async def register_user(
    data: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new user account. Only admins can register new users.
    """
    # Check for existing username
    if auth_service.get_user_by_username(db, data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{data.username}' already exists",
        )

    # Check for existing email
    if auth_service.get_user_by_email(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{data.email}' already registered",
        )

    user = auth_service.register_user(db, data)
    return user


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """Return the profile of the currently authenticated user."""
    return current_user
