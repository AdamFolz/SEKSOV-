"""User schemas."""

from pydantic import BaseModel
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema."""
    username: str
    email: str | None = None
    is_active: bool = True


class UserCreate(UserBase):
    """User creation schema."""
    pass


class UserUpdate(BaseModel):
    """User update schema."""
    email: str | None = None
    is_active: bool | None = None


class User(UserBase):
    """User response schema."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
