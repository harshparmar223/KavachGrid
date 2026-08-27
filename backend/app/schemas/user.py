"""
KAVACHGRID 3.0 — User Pydantic Schemas
Phase 2: Request/Response validation models for Users

Schemas:
    - UserCreate: Registration input
    - UserUpdate: Partial update input
    - UserResponse: API response output
    - UserLogin: Authentication input
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Shared user fields."""

    username: str = Field(..., min_length=3, max_length=50, examples=["operator1"])
    email: str = Field(..., max_length=255, examples=["operator1@kavachgrid.in"])
    full_name: str = Field(..., min_length=1, max_length=100, examples=["Grid Operator"])
    role: str = Field(
        default="viewer",
        pattern="^(admin|operator|investigator|viewer)$",
        examples=["operator"],
    )


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., min_length=8, max_length=128, examples=["SecurePass123!"])


class UserUpdate(BaseModel):
    """Schema for partially updating a user."""

    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[str] = Field(None, pattern="^(admin|operator|investigator|viewer)$")
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128)


class UserResponse(UserBase):
    """Schema for user API responses."""

    id: UUID
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    """Schema for user login."""

    username: str = Field(..., examples=["admin"])
    password: str = Field(..., examples=["SecurePass123!"])
