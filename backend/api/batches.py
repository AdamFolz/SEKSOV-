"""Batch endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas.batch import Batch, BatchCreate, BatchUpdate

router = APIRouter(prefix="/api/batches", tags=["batches"])


@router.get("/")
async def list_batches(db: Session = Depends(get_db)):
    """List all active batches."""
    return {"message": "List batches endpoint - coming soon"}


@router.post("/")
async def create_batch(batch: BatchCreate, db: Session = Depends(get_db)):
    """Create a new batch."""
    return {"message": "Create batch endpoint - coming soon", "batch": batch}


@router.get("/{batch_id}")
async def get_batch(batch_id: int, db: Session = Depends(get_db)):
    """Get a specific batch."""
    return {"message": f"Get batch {batch_id} endpoint - coming soon"}


@router.put("/{batch_id}")
async def update_batch(batch_id: int, batch: BatchUpdate, db: Session = Depends(get_db)):
    """Update a batch."""
    return {"message": f"Update batch {batch_id} endpoint - coming soon"}


@router.delete("/{batch_id}")
async def delete_batch(batch_id: int, db: Session = Depends(get_db)):
    """Delete a batch."""
    return {"message": f"Delete batch {batch_id} endpoint - coming soon"}
