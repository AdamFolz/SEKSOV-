"""Injection endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas.injection import Injection, InjectionCreate

router = APIRouter(prefix="/api/injections", tags=["injections"])


@router.get("/")
async def list_injections(batch_id: int | None = None, db: Session = Depends(get_db)):
    """List injections, optionally filtered by batch."""
    return {"message": "List injections endpoint - coming soon"}


@router.post("/")
async def create_injection(injection: InjectionCreate, db: Session = Depends(get_db)):
    """Record a new injection."""
    return {"message": "Create injection endpoint - coming soon", "injection": injection}


@router.get("/{injection_id}")
async def get_injection(injection_id: int, db: Session = Depends(get_db)):
    """Get a specific injection."""
    return {"message": f"Get injection {injection_id} endpoint - coming soon"}


@router.delete("/{injection_id}")
async def delete_injection(injection_id: int, db: Session = Depends(get_db)):
    """Delete an injection record."""
    return {"message": f"Delete injection {injection_id} endpoint - coming soon"}
