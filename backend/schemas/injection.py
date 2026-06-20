"""Injection schemas."""

from pydantic import BaseModel
from datetime import datetime


class InjectionBase(BaseModel):
    """Base injection schema."""
    volume_ml: float
    method: str
    location: str
    notes: str | None = None


class InjectionCreate(InjectionBase):
    """Injection creation schema."""
    batch_id: int
    user_id: int


class Injection(InjectionBase):
    """Injection response schema."""
    id: int
    batch_id: int
    user_id: int
    remaining_after_injection_ml: float
    created_at: datetime
    
    class Config:
        from_attributes = True
