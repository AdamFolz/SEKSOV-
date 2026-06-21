"""Batch model for solution batches."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Batch(Base):
    """Batch model for tracking solution batches."""
    
    __tablename__ = "batches"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    medication_name = Column(String, index=True)
    total_volume_ml = Column(Float)
    remaining_volume_ml = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="batches")
    injections = relationship("Injection", back_populates="batch", cascade="all, delete-orphan")
