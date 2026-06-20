"""Injection CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.injection import Injection as InjectionModel
from models.batch import Batch as BatchModel
from schemas.injection import Injection as InjectionSchema, InjectionCreate
from api.auth import get_current_user_from_token

router = APIRouter(prefix="/api/injections", tags=["injections"])


@router.get("/", response_model=list[InjectionSchema])
async def list_injections(
    batch_id: int | None = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_token)
):
    """List injections for current user, optionally filtered by batch."""
    query = db.query(InjectionModel).filter(
        InjectionModel.user_id == current_user.id
    )
    
    if batch_id:
        query = query.filter(InjectionModel.batch_id == batch_id)
    
    injections = query.order_by(InjectionModel.created_at.desc()).all()
    return injections


@router.post("/", response_model=InjectionSchema)
async def create_injection(
    injection: InjectionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_token)
):
    """Record a new injection."""
    # Verify batch exists and belongs to user
    batch = db.query(BatchModel).filter(
        BatchModel.id == injection.batch_id,
        BatchModel.user_id == current_user.id
    ).first()
    
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )
    
    if not batch.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch is not active"
        )
    
    # Check if volume is valid
    if injection.volume_ml > batch.remaining_volume_ml:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Injection volume ({injection.volume_ml}ml) exceeds remaining volume ({batch.remaining_volume_ml}ml)"
        )
    
    # Calculate remaining volume after injection
    remaining_after = batch.remaining_volume_ml - injection.volume_ml
    
    # Create injection record
    db_injection = InjectionModel(
        batch_id=injection.batch_id,
        user_id=current_user.id,
        volume_ml=injection.volume_ml,
        method=injection.method,
        location=injection.location,
        remaining_after_injection_ml=remaining_after,
        notes=injection.notes
    )
    
    # Update batch remaining volume
    batch.remaining_volume_ml = remaining_after
    
    db.add(db_injection)
    db.commit()
    db.refresh(db_injection)
    return db_injection


@router.get("/{injection_id}", response_model=InjectionSchema)
async def get_injection(
    injection_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_token)
):
    """Get a specific injection."""
    injection = db.query(InjectionModel).filter(
        InjectionModel.id == injection_id,
        InjectionModel.user_id == current_user.id
    ).first()
    
    if not injection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Injection not found"
        )
    return injection


@router.delete("/{injection_id}")
async def delete_injection(
    injection_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_token)
):
    """Delete an injection record."""
    injection = db.query(InjectionModel).filter(
        InjectionModel.id == injection_id,
        InjectionModel.user_id == current_user.id
    ).first()
    
    if not injection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Injection not found"
        )
    
    # Restore batch volume if deleting injection
    batch = db.query(BatchModel).filter(
        BatchModel.id == injection.batch_id
    ).first()
    
    if batch:
        batch.remaining_volume_ml += injection.volume_ml
    
    db.delete(injection)
    db.commit()
    
    return {"message": "Injection deleted successfully"}
