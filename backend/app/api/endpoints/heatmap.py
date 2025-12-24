"""Heatmap API Endpoints - Time tracking heatmap visualization"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session as DBSession
from datetime import datetime, timezone, timedelta, date as DateType, time as TimeType
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
    category_id: Optional[int] = Query(None, description="Filter by category id"),
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
    # Default to last 180 days to reduce payload and query volume
    now = datetime.now(timezone.utc)
    
    if end is None:
        end_date = now.date()
    else:
        end_date = end
    
    if start is None:
        start_date = end_date - timedelta(days=180)
    else:
        start_date = start
    
    # Validate date range
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start date must be before or equal to end date"
        )
    
    # Compute datetime bounds once so the filter can use an index on start_time
    start_dt = datetime.combine(start_date, TimeType.min).replace(tzinfo=timezone.utc)
    end_dt = datetime.combine(end_date, TimeType.max).replace(tzinfo=timezone.utc)

    # Query sessions grouped by date
    query = db.query(
        func.date(Session.start_time).label("date"),
        func.coalesce(func.sum(func.coalesce(Session.effective_seconds, Session.duration_seconds)), 0).label("total_seconds")
    ).filter(
        Session.user_id == current_user.id,
        Session.end_time.isnot(None),  # Only completed sessions
        Session.start_time >= start_dt,
        Session.start_time <= end_dt
    )

    if category_id is not None:
        query = query.filter(Session.category_id == category_id)

    results = query.group_by(
        func.date(Session.start_time)
    ).order_by(
        func.date(Session.start_time)
    ).all()
    
    # Convert to response format
    heatmap_data = [
        HeatmapDay(
            # Convert date object to ISO string to satisfy schema validation
            date=row.date.isoformat(),
            total_seconds=int(row.total_seconds)
        )
        for row in results
    ]
    
    return heatmap_data


@router.get("/day", response_model=List[DaySessionDetail])
def get_day_sessions(
    date: DateType = Query(..., description="Date to query (YYYY-MM-DD)"),
    category_id: Optional[int] = Query(None, description="Filter by category id"),
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
    day_start = datetime.combine(date, TimeType.min).replace(tzinfo=timezone.utc)
    day_end = datetime.combine(date, TimeType.max).replace(tzinfo=timezone.utc)

    # Query sessions for the specific date
    sessions_query = db.query(
        Session.id,
        Session.category_id,
        Category.name.label("category_name"),
        Session.start_time,
        Session.end_time,
        Session.duration_seconds,
        Session.effective_seconds,
        Session.note,
        Session.source
    ).outerjoin(
        Category, Session.category_id == Category.id
    ).filter(
        Session.user_id == current_user.id,
        Session.end_time.isnot(None),  # Only completed sessions
        Session.start_time >= day_start,
        Session.start_time <= day_end
    )

    if category_id is not None:
        sessions_query = sessions_query.filter(Session.category_id == category_id)

    sessions = sessions_query.order_by(
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
            effective_seconds=s.effective_seconds if s.effective_seconds is not None else s.duration_seconds,
            note=s.note,
            source=s.source
        )
        for s in sessions
    ]
    
    return session_details
