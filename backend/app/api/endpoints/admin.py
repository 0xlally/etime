"""Admin API Endpoints - User and session management for admins"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import or_, and_, func
from typing import Optional
from datetime import datetime

from app.models.user import User, UserRole
from app.models.session import Session as SessionModel
from app.models.user import User
from app.models.admin_audit_log import AdminAuditLog
from app.schemas.admin import (
    UserUpdateByAdmin, UserListResponse, PaginatedUsersResponse,
    SessionListItemResponse, PaginatedSessionsResponse
)
from app.api.deps import get_current_admin
from app.core.db import get_db


router = APIRouter()


def create_audit_log(
    db: DBSession,
    admin_user_id: int,
    action: str,
    target_type: str,
    target_id: int,
    detail_json: Optional[dict] = None
):
    """Helper function to create audit log entry"""
    log = AdminAuditLog(
        admin_user_id=admin_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail_json=detail_json
    )
    db.add(log)
    db.commit()


@router.get("/users", response_model=PaginatedUsersResponse)
def list_users(
    search: Optional[str] = Query(None, description="Search by username or email"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_admin: User = Depends(get_current_admin),
    db: DBSession = Depends(get_db)
):
    """
    List all users with pagination and optional search.
    
    Admin only. Searches across username and email fields.
    
    Args:
        search: Optional search query for username/email
        page: Page number (starting from 1)
        page_size: Number of items per page (max 100)
        current_admin: Current admin user
        db: Database session
        
    Returns:
        Paginated list of users
    """
    # Build query
    query = db.query(User)
    
    # Apply search filter if provided
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                User.username.ilike(search_pattern),
                User.email.ilike(search_pattern)
            )
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    users = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()
    
    return PaginatedUsersResponse(
        total=total,
        page=page,
        page_size=page_size,
        users=[UserListResponse.from_orm(user) for user in users]
    )


@router.patch("/users/{user_id}", response_model=UserListResponse)
def update_user(
    user_id: int,
    update_data: UserUpdateByAdmin,
    current_admin: User = Depends(get_current_admin),
    db: DBSession = Depends(get_db)
):
    """
    Update user attributes (is_active, role).
    
    Admin only. Creates audit log for the operation.
    
    Args:
        user_id: ID of user to update
        update_data: Fields to update
        current_admin: Current admin user
        db: Database session
        
    Returns:
        Updated user
        
    Raises:
        HTTPException: If user not found
    """
    # Find user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Track changes for audit log
    changes = {}
    
    # Update fields
    if update_data.is_active is not None:
        old_value = user.is_active
        user.is_active = update_data.is_active
        changes["is_active"] = {"old": old_value, "new": update_data.is_active}
    
    if update_data.role is not None:
        old_value = user.role.value if isinstance(user.role, UserRole) else user.role
        user.role = update_data.role
        changes["role"] = {"old": old_value, "new": update_data.role}
    
    # Commit changes
    db.commit()
    db.refresh(user)
    
    # Create audit log
    create_audit_log(
        db=db,
        admin_user_id=current_admin.id,
        action="update_user",
        target_type="user",
        target_id=user_id,
        detail_json={"changes": changes}
    )
    
    return UserListResponse.from_orm(user)


@router.get("/sessions", response_model=PaginatedSessionsResponse)
def list_sessions(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    start: Optional[str] = Query(None, description="Filter by start time (>=) in ISO format"),
    end: Optional[str] = Query(None, description="Filter by end time (<=) in ISO format"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_admin: User = Depends(get_current_admin),
    db: DBSession = Depends(get_db)
):
    """
    List sessions with filters and pagination.
    
    Admin only. Supports filtering by user, time range, and category.
    
    Args:
        user_id: Optional filter by user ID
        start: Optional filter by start time (inclusive)
        end: Optional filter by end time (inclusive)
        category_id: Optional filter by category ID
        page: Page number (starting from 1)
        page_size: Number of items per page (max 100)
        current_admin: Current admin user
        db: Database session
        
    Returns:
        Paginated list of sessions
    """
    # Build query
    query = db.query(SessionModel)
    
    # Apply filters
    if user_id is not None:
        query = query.filter(SessionModel.user_id == user_id)
    
    if start is not None:
        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
        query = query.filter(SessionModel.start_time >= start_dt)
    
    if end is not None:
        end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
        query = query.filter(SessionModel.start_time <= end_dt)
    
    if category_id is not None:
        query = query.filter(SessionModel.category_id == category_id)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    sessions = query.order_by(SessionModel.start_time.desc()).offset(offset).limit(page_size).all()

    # Fetch usernames to avoid N+1
    user_ids = {s.user_id for s in sessions}
    user_map = {u.id: u.username for u in db.query(User.id, User.username).filter(User.id.in_(user_ids)).all()}

    session_items = [
        SessionListItemResponse(
          id=s.id,
          user_id=s.user_id,
          username=user_map.get(s.user_id),
          category_id=s.category_id,
          start_time=s.start_time,
          end_time=s.end_time,
          duration_seconds=s.duration_seconds,
          note=s.note,
          source=s.source,
          created_at=s.created_at,
        )
        for s in sessions
    ]
    
    return PaginatedSessionsResponse(
        total=total,
        page=page,
        page_size=page_size,
        sessions=session_items
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: int,
    current_admin: User = Depends(get_current_admin),
    db: DBSession = Depends(get_db)
):
    """
    Delete a session (soft delete preferred if model supports it).
    
    Admin only. Creates audit log for the operation.
    
    Args:
        session_id: ID of session to delete
        current_admin: Current admin user
        db: Database session
        
    Raises:
        HTTPException: If session not found
    """
    # Find session
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Store session info for audit log before deletion
    session_info = {
        "user_id": session.user_id,
        "start_time": session.start_time.isoformat() if session.start_time else None,
        "end_time": session.end_time.isoformat() if session.end_time else None,
        "duration_seconds": session.duration_seconds,
        "category_id": session.category_id
    }
    
    # Delete session (hard delete since model doesn't have soft delete flag)
    db.delete(session)
    db.commit()
    
    # Create audit log
    create_audit_log(
        db=db,
        admin_user_id=current_admin.id,
        action="delete_session",
        target_type="session",
        target_id=session_id,
        detail_json={"deleted_session": session_info}
    )


@router.post("/users/{user_id}/reset-password", status_code=status.HTTP_200_OK)
def reset_user_password(
    user_id: int,
    password_data: dict,
    current_admin: User = Depends(get_current_admin),
    db: DBSession = Depends(get_db)
):
    """
    Reset a user's password.
    
    Admin only. Creates audit log for the operation.
    
    Args:
        user_id: ID of user to reset password for
        password_data: Dict with 'new_password' field
        current_admin: Current admin user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user not found or password invalid
    """
    from app.utils.security import hash_password
    
    # Find user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    new_password = password_data.get("new_password")
    if not new_password or len(new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters"
        )
    
    # Update password
    user.password_hash = hash_password(new_password)
    db.commit()
    
    # Create audit log
    create_audit_log(
        db=db,
        admin_user_id=current_admin.id,
        action="reset_password",
        target_type="user",
        target_id=user_id,
        detail_json={"username": user.username}
    )
    
    return {"message": "Password reset successfully"}


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin),
    db: DBSession = Depends(get_db)
):
    """
    Delete a user account.
    
    Admin only. Creates audit log for the operation.
    Cannot delete yourself or other admins.
    
    Args:
        user_id: ID of user to delete
        current_admin: Current admin user
        db: Database session
        
    Raises:
        HTTPException: If user not found or attempting to delete admin/self
    """
    # Find user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deleting yourself
    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Prevent deleting other admins
    if user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete admin users"
        )
    
    # Store user info for audit log
    user_info = {
        "username": user.username,
        "email": user.email,
        "role": user.role.value if isinstance(user.role, UserRole) else user.role
    }
    
    # Delete user (cascade delete will handle related records)
    db.delete(user)
    db.commit()
    
    # Create audit log
    create_audit_log(
        db=db,
        admin_user_id=current_admin.id,
        action="delete_user",
        target_type="user",
        target_id=user_id,
        detail_json={"deleted_user": user_info}
    )


@router.get("/audit-logs", response_model=list)
def list_audit_logs(
    limit: int = Query(100, ge=1, le=500, description="Number of logs to return"),
    current_admin: User = Depends(get_current_admin),
    db: DBSession = Depends(get_db)
):
    """
    List audit logs.
    
    Admin only. Returns recent audit logs ordered by creation time.
    
    Args:
        limit: Maximum number of logs to return (default 100, max 500)
        current_admin: Current admin user
        db: Database session
        
    Returns:
        List of audit logs
    """
    from app.schemas.admin import AuditLogResponse
    
    logs = db.query(AdminAuditLog).order_by(
        AdminAuditLog.created_at.desc()
    ).limit(limit).all()
    
    return [AuditLogResponse.from_orm(log) for log in logs]
