"""User Endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.user import User
from app.schemas.user import UserResponse
from app.api.deps import get_current_active_user, get_current_admin

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information.
    
    Requires valid JWT token in Authorization header.
    
    Args:
        current_user: Current authenticated user from dependency
        
    Returns:
        Current user information
    """
    return current_user


@router.get("/admin-only")
def admin_only_route(
    current_admin: User = Depends(get_current_admin)
):
    """
    Example endpoint that requires admin privileges.
    
    Args:
        current_admin: Current admin user from dependency
        
    Returns:
        Admin-only message
    """
    return {
        "message": "This is an admin-only endpoint",
        "admin_user": current_admin.username
    }
