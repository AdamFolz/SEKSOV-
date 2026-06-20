"""User endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas.user import User, UserCreate, UserUpdate

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/")
async def list_users(db: Session = Depends(get_db)):
    """List all users."""
    return {"message": "List users endpoint - coming soon"}


@router.post("/")
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user."""
    return {"message": "Create user endpoint - coming soon", "user": user}


@router.get("/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user."""
    return {"message": f"Get user {user_id} endpoint - coming soon"}


@router.put("/{user_id}")
async def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    """Update a user."""
    return {"message": f"Update user {user_id} endpoint - coming soon"}


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user."""
    return {"message": f"Delete user {user_id} endpoint - coming soon"}
