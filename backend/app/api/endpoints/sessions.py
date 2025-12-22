"""Session Endpoints - Time tracking sessions"""
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import and_
from app.core.db import get_db
from app.models.user import User
from app.models.category import Category
from app.models.session import Session, SessionSource
from app.schemas.session import (
    SessionStart, SessionStop, SessionManual, 
    SessionResponse, ActiveSessionResponse
)
from app.api.deps import get_current_active_user

router = APIRouter()


def _validate_category_ownership(category_id: Optional[int], user_id: int, db: DBSession) -> None:
    """
    Validate that category belongs to the user.
    
    Args:
        category_id: Category ID to validate
        user_id: User ID
        db: Database session
        
    Raises:
        HTTPException: If category doesn't exist or doesn't belong to user
    """
    if category_id is None:
        return
    
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    if category.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to use this category"
        )


def _get_active_session(user_id: int, db: DBSession) -> Optional[Session]:
    """Get user's active (ongoing) session if exists."""
    return db.query(Session).filter(
        Session.user_id == user_id,
        Session.end_time.is_(None)
    ).first()


@router.post("/start", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def start_session(
    session_data: SessionStart,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db)
):
    """
    Start a new timer session.
    
    Only one session can be active at a time per user.
    
    Args:
        session_data: Session start data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created session
        
    Raises:
        HTTPException: If user already has an active session or category doesn't belong to user
    """
    # Check if user already has an active session
    active_session = _get_active_session(current_user.id, db)
    if active_session:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an active session. Please stop it before starting a new one."
        )
    
    # Validate category ownership
    _validate_category_ownership(session_data.category_id, current_user.id, db)
    
    # Create new session
    new_session = Session(
        user_id=current_user.id,
        category_id=session_data.category_id,
        start_time=datetime.now(timezone.utc),
        note=session_data.note,
        source=SessionSource.TIMER.value
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return new_session


@router.post("/stop", response_model=SessionResponse)
def stop_session(
    session_data: SessionStop,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db)
):
    """
    Stop the current active timer session.
    
    Args:
        session_data: Session stop data (optional note)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Stopped session with calculated duration
        
    Raises:
        HTTPException: If no active session exists
    """
    # Get active session
    active_session = _get_active_session(current_user.id, db)
    if not active_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active session found"
        )
    
    # Stop the session
    now = datetime.now(timezone.utc)
    active_session.end_time = now
    
    # Ensure start_time has timezone (SQLite stores as naive)
    start_time = active_session.start_time
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    
    # Calculate duration in seconds
    duration = (now - start_time).total_seconds()
    active_session.duration_seconds = int(duration)
    
    # Update note if provided
    if session_data.note:
        active_session.note = session_data.note
    
    db.commit()
    db.refresh(active_session)
    
    return active_session


@router.post("/manual", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_manual_session(
    session_data: SessionManual,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db)
):
    """
    Manually create a completed session.
    
    Useful for adding historical time tracking data.
    
    Args:
        session_data: Manual session data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created session
        
    Raises:
        HTTPException: If category doesn't belong to user or end_time <= start_time
    """
    # Validate category ownership
    _validate_category_ownership(session_data.category_id, current_user.id, db)
    
    start = session_data.start_time
    end = session_data.end_time
    
    # If the session spans multiple days, split into per-day sessions
    sessions_created = []
    cursor = start
    while cursor.date() < end.date():
        # End of current day 23:59:59
        day_end = cursor.replace(hour=23, minute=59, second=59, microsecond=999999)
        duration = (day_end - cursor).total_seconds()
        partial = Session(
            user_id=current_user.id,
            category_id=session_data.category_id,
            start_time=cursor,
            end_time=day_end,
            duration_seconds=int(duration),
            note=session_data.note,
            source=SessionSource.MANUAL.value
        )
        db.add(partial)
        sessions_created.append(partial)
        # Move cursor to start of next day
        cursor = day_end.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    # Last segment (same day or remaining part)
    duration_last = (end - cursor).total_seconds()
    last_segment = Session(
        user_id=current_user.id,
        category_id=session_data.category_id,
        start_time=cursor,
        end_time=end,
        duration_seconds=int(duration_last),
        note=session_data.note,
        source=SessionSource.MANUAL.value
    )
    db.add(last_segment)
    sessions_created.append(last_segment)
    
    db.commit()
    for s in sessions_created:
        db.refresh(s)
    
    # Return the last segment for simplicity
    return last_segment


@router.get("/active", response_model=Optional[ActiveSessionResponse])
def get_active_session(
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db)
):
    """
    Get the current active session if exists.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Active session or None
    """
    active_session = _get_active_session(current_user.id, db)
    
    if not active_session:
        return None
    
    # Ensure start_time has timezone (SQLite stores as naive)
    start_time = active_session.start_time
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    
    # Calculate elapsed time
    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
    
    return ActiveSessionResponse(
        id=active_session.id,
        user_id=active_session.user_id,
        category_id=active_session.category_id,
        start_time=active_session.start_time,
        note=active_session.note,
        elapsed_seconds=int(elapsed)
    )


@router.get("", response_model=List[SessionResponse])
def list_sessions(
    start: Optional[datetime] = Query(None, description="Filter sessions starting from this time"),
    end: Optional[datetime] = Query(None, description="Filter sessions ending before this time"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    include_active: bool = Query(False, description="Include active (ongoing) sessions"),
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db)
):
    """
    Get user's sessions with optional filtering.
    
    Args:
        start: Filter sessions that started on or after this time
        end: Filter sessions that ended on or before this time
        category_id: Filter by specific category
        include_active: Whether to include ongoing sessions
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of sessions matching filters
    """
    # Base query - only user's sessions
    query = db.query(Session).filter(Session.user_id == current_user.id)
    
    # Apply filters
    if start:
        query = query.filter(Session.start_time >= start)
    
    if end:
        query = query.filter(Session.start_time <= end)
    
    if category_id is not None:
        query = query.filter(Session.category_id == category_id)
    
    if not include_active:
        query = query.filter(Session.end_time.isnot(None))
    
    # Order by start time descending
    sessions = query.order_by(Session.start_time.desc()).all()
    
    return sessions


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db)
):
    """
    Get a specific session by ID.
    
    Args:
        session_id: Session ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Session details
        
    Raises:
        HTTPException: If session not found or doesn't belong to user
    """
    session = db.query(Session).filter(Session.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Verify ownership
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this session"
        )
    
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db)
):
    """
    Delete a session.
    
    Args:
        session_id: Session ID
        current_user: Current authenticated user
        db: Database session
        
    Raises:
        HTTPException: If session not found or doesn't belong to user
    """
    session = db.query(Session).filter(Session.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Verify ownership
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this session"
        )
    
    db.delete(session)
    db.commit()
    
    return None
