"""Heatmap API Endpoints - Time tracking heatmap visualization"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import func, Date
from sqlalchemy.orm import Session as DBSession
from datetime import datetime, timezone, timedelta, date as DateType
from typing import Optional, List

from app.models.user import User
from app.models.session import Session
from app.models.category import Category
from app.schemas.heatmap import HeatmapDay, DaySessionDetail
from app.api.deps import get_current_active_user
from app.core.db import get_db


router = APIRouter()


@router.get("", response_model=List[HeatmapDay])
def get_heatmap(
    start: Optional[DateType] = Query(None, description="Start date (YYYY-MM-DD)"),
    end: Optional[DateType] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db)
):
    """
    Get heatmap data for a date range.
    
    Returns daily aggregated time tracking data suitable for heatmap visualization.
    
    Query parameters:
    - start: Start date (defaults to 365 days ago)
    - end: End date (defaults to today)
    
    Returns:
    - Array of {date, total_seconds} for each day in range
    
    Note: Dates are in UTC. Only completed sessions are counted.
    """
    # Default to last 365 days
    now = datetime.now(timezone.utc)
    
    if end is None:
        end_date = now.date()
    else:
        end_date = end
    
    if start is None:
        start_date = end_date - timedelta(days=365)
    else:
        start_date = start
    
    # Validate date range
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start date must be before or equal to end date"
        )
    
    # Query sessions grouped by date
    # We need to extract the date part from start_time
    # For SQLite, we use date() function
    results = db.query(
        func.date(Session.start_time).label("date"),
        func.coalesce(func.sum(Session.duration_seconds), 0).label("total_seconds")
    ).filter(
        Session.user_id == current_user.id,
        Session.end_time.isnot(None),  # Only completed sessions
        func.date(Session.start_time) >= start_date,
        func.date(Session.start_time) <= end_date
    ).group_by(
        func.date(Session.start_time)
    ).order_by(
        func.date(Session.start_time)
    ).all()
    
    # Convert to response format
    heatmap_data = [
        HeatmapDay(
            date=row.date,
            total_seconds=int(row.total_seconds)
        )
        for row in results
    ]
    
    return heatmap_data


@router.get("/day", response_model=List[DaySessionDetail])
def get_day_sessions(
    date: DateType = Query(..., description="Date to query (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db)
):
    """
    Get detailed sessions for a specific day.
    
    Returns all completed sessions that started on the specified date,
    including category information.
    
    Query parameters:
    - date: Date to query (YYYY-MM-DD, required)
    
    Returns:
    - Array of session details with category names
    
    Note: Date is in UTC.
    """
    # Query sessions for the specific date
    sessions = db.query(
        Session.id,
        Session.category_id,
        Category.name.label("category_name"),
        Session.start_time,
        Session.end_time,
        Session.duration_seconds,
        Session.note,
        Session.source
    ).outerjoin(
        Category, Session.category_id == Category.id
    ).filter(
        Session.user_id == current_user.id,
        Session.end_time.isnot(None),  # Only completed sessions
        func.date(Session.start_time) == date
    ).order_by(
        Session.start_time
    ).all()
    
    # Convert to response format
    session_details = [
        DaySessionDetail(
            id=s.id,
            category_id=s.category_id,
            category_name=s.category_name,
            start_time=s.start_time if s.start_time.tzinfo else s.start_time.replace(tzinfo=timezone.utc),
            end_time=s.end_time if s.end_time.tzinfo else s.end_time.replace(tzinfo=timezone.utc),
            duration_seconds=s.duration_seconds,
            note=s.note,
            source=s.source
        )
        for s in sessions
    ]
    
    return session_details
