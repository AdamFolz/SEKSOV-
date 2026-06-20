"""Batch CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models.batch import Batch as BatchModel
from schemas.batch import Batch as BatchSchema, BatchCreate, BatchUpdate
from api.auth import get_current_user_from_token

router = APIRouter(prefix="/api/batches", tags=["batches"])


@router.get("/", response_model=list[BatchSchema])
async def list_batches(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_token)
):
    """List all batches for current user."""
    batches = db.query(BatchModel).filter(
        BatchModel.user_id == current_user.id
    ).all()
    return batches


@router.post("/", response_model=BatchSchema)
async def create_batch(
    batch: BatchCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_token)
):
    """Create a new batch."""
    # Check if user already has an active batch
    active_batch = db.query(BatchModel).filter(
        BatchModel.user_id == current_user.id,
        BatchModel.is_active == True
    ).first()
    
    if active_batch:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an active batch"
        )
    
    db_batch = BatchModel(
        user_id=current_user.id,
        medication_name=batch.medication_name,
        total_volume_ml=batch.total_volume_ml,
        remaining_volume_ml=batch.total_volume_ml
    )
    db.add(db_batch)
    db.commit()
    db.refresh(db_batch)
    return db_batch


@router.get("/{batch_id}", response_model=BatchSchema)
async def get_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_token)
):
    """Get a specific batch."""
    batch = db.query(BatchModel).filter(
        BatchModel.id == batch_id,
        BatchModel.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )
    return batch


@router.put("/{batch_id}", response_model=BatchSchema)
async def update_batch(
    batch_id: int,
    batch_update: BatchUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_token)
):
    """Update a batch."""
    batch = db.query(BatchModel).filter(
        BatchModel.id == batch_id,
        BatchModel.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )
    
    if batch_update.medication_name:
        batch.medication_name = batch_update.medication_name
    
    if batch_update.is_active is not None:
        if batch_update.is_active == False:
            batch.completed_at = datetime.utcnow()
        batch.is_active = batch_update.is_active
    
    db.commit()
    db.refresh(batch)
    return batch


@router.delete("/{batch_id}")
async def delete_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_token)
):
    """Delete a batch."""
    batch = db.query(BatchModel).filter(
        BatchModel.id == batch_id,
        BatchModel.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )
    
    db.delete(batch)
    db.commit()
    return {"message": "Batch deleted successfully"}
