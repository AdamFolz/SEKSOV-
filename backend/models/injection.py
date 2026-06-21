"""Injection model for tracking medication injections."""

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Injection(Base):
    """Injection model for tracking individual injections."""
    
    __tablename__ = "injections"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    volume_ml = Column(Float)
    method = Column(String)  # e.g., 'intramuscular', 'subcutaneous'
    location = Column(String)  # e.g., 'left arm', 'right arm'
    remaining_after_injection_ml = Column(Float)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    batch = relationship("Batch", back_populates="injections")
    user = relationship("User", back_populates="injections")
