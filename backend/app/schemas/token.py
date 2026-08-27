"""
KAVACHGRID 3.0 — Token Pydantic Schemas
Phase 5: JWT authentication tokens

Schemas:
    - Token: Login response containing the access token
    - TokenPayload: Decoded JWT payload (internal use)
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Token(BaseModel):
    """Login response containing the JWT access token."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenPayload(BaseModel):
    """Decoded JWT token payload (internal use)."""

    sub: str = Field(..., description="User UUID as string")
    role: str = Field(..., description="User role")
    exp: Optional[datetime] = Field(None, description="Token expiration time")
