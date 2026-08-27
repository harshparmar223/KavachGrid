"""
KAVACHGRID 3.0 — Auth Service
Phase 5: User authentication and registration

Handles:
    - User authentication (username + password verification)
    - User registration with password hashing
    - Last login timestamp updates
"""

from datetime import datetime, timezone
from typing import Optional
import uuid

from sqlalchemy.orm import Session

from app.db.models import User
from app.schemas.user import UserCreate
from app.utils.security import hash_password, verify_password


class AuthService:
    """Service layer for user authentication and registration."""

    @staticmethod
    def authenticate_user(
        db: Session,
        username: str,
        password: str,
    ) -> Optional[User]:
        """
        Verify user credentials and return the User if valid.

        Returns None if the username doesn't exist or password is incorrect.
        """
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def register_user(db: Session, data: UserCreate) -> User:
        """
        Create a new user with a hashed password.

        Raises an exception if the username or email already exists
        (handled by the database unique constraint).
        """
        now = datetime.now(timezone.utc)
        user = User(
            id=uuid.uuid4(),
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=data.role,
            is_active=True,
            created_at=now,
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Fetch a user by username."""
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Fetch a user by email."""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def update_last_login(db: Session, user_id: uuid.UUID) -> Optional[User]:
        """Stamp the last_login_at timestamp for a user."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        user.last_login_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        return user


auth_service = AuthService()
