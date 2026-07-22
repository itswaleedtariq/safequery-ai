from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserSignupRequest(BaseModel):
    """Information required to create an account."""

    name: str = Field(
        min_length=2,
        max_length=120,
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )


class UserLoginRequest(BaseModel):
    """Email and password submitted during login."""

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )


class UserResponse(BaseModel):
    """Public user information."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    name: str
    email: EmailStr
    is_active: bool
    created_at: datetime


class AccessTokenResponse(BaseModel):
    """JWT token and authenticated user information."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse