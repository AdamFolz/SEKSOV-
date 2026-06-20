"""Batch schemas."""

from pydantic import BaseModel
from datetime import datetime


class BatchBase(BaseModel):
    """Base batch schema."""
    medication_name: str
    total_volume_ml: float


class BatchCreate(BatchBase):
    """Batch creation schema."""
    pass


class BatchUpdate(BaseModel):
    """Batch update schema."""
    medication_name: str | None = None
    is_active: bool | None = None


class Batch(BatchBase):
    """Batch response schema."""
    id: int
    user_id: int
    remaining_volume_ml: float
    is_active: bool
    created_at: datetime
    completed_at: datetime | None = None
    
    class Config:
        from_attributes = True
