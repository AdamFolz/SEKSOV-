"""User CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models.user import User as UserModel
from schemas.auth import User as UserSchema

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/", response_model=list[UserSchema])
async def list_users(db: Session = Depends(get_db)):
    """List all users."""
    users = db.query(UserModel).all()
    return users


@router.get("/{user_id}", response_model=UserSchema)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID."""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user
