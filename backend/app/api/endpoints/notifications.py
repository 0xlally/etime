"""Notifications API Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession
from datetime import datetime, timezone
from typing import List

from app.models.user import User
from app.models.notification import Notification
from app.schemas.work_target import NotificationResponse
from app.api.deps import get_current_active_user
from app.core.db import get_db


router = APIRouter()


@router.get("", response_model=List[NotificationResponse])
def list_notifications(
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db)
):
    """
    List all notifications for the current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of notifications (unread first, then by created_at desc)
    """
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(
        Notification.read_at.is_(None).desc(),  # Unread first
        Notification.created_at.desc()
    ).all()
    
    return notifications


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db)
):
    """
    Mark a notification as read.
    
    Args:
        notification_id: Notification ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated notification
        
    Raises:
        HTTPException: If notification not found or not owned by user
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    # Mark as read
    if notification.read_at is None:
        notification.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notification)
    
    return notification
