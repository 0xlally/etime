"""Stats API Endpoints - Time tracking statistics"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session as DBSession
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.models.user import User
from app.models.session import Session
from app.models.category import Category
from app.schemas.stats import StatsSummary, CategoryStats
from app.api.deps import get_current_active_user
from app.core.db import get_db


router = APIRouter()


def _get_time_range(
    range_type: Optional[str],
    start: Optional[datetime],
    end: Optional[datetime]
) -> tuple[datetime, datetime]:
    """
    Calculate time range based on range type or explicit start/end.
    
    Args:
        range_type: Preset range (today, week, month)
        start: Custom start datetime
        end: Custom end datetime
        
    Returns:
        Tuple of (start_datetime, end_datetime)
        
    Raises:
        HTTPException: If parameters are invalid
    """
    now = datetime.now(timezone.utc)
    
    if range_type:
        if range_type == "today":
            # Today from 00:00:00 to 23:59:59
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif range_type == "week":
            # This week from Monday 00:00:00 to Sunday 23:59:59
            # weekday() returns 0 for Monday, 6 for Sunday
            days_since_monday = now.weekday()
            monday = now - timedelta(days=days_since_monday)
            start_time = monday.replace(hour=0, minute=0, second=0, microsecond=0)
            sunday = monday + timedelta(days=6)
            end_time = sunday.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif range_type == "month":
            # This month from 1st 00:00:00 to last day 23:59:59
            start_time = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Get last day of month
            if now.month == 12:
                next_month = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_month = now.replace(month=now.month + 1, day=1)
            last_day = next_month - timedelta(days=1)
            end_time = last_day.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid range type: {range_type}. Must be 'today', 'week', or 'month'"
            )
        return start_time, end_time
    
    elif start and end:
        # Custom range
        if start >= end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start must be before end"
            )
        return start, end
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'range' or both 'start' and 'end' must be provided"
        )


@router.get("/summary", response_model=StatsSummary)
def get_stats_summary(
    range_type: Optional[str] = Query(None, alias="range", description="Preset range: today, week, or month"),
    start: Optional[datetime] = Query(None, description="Custom start datetime (UTC)"),
    end: Optional[datetime] = Query(None, description="Custom end datetime (UTC)"),
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db)
):
    """
    Get time tracking statistics summary.
    
    Query parameters:
    - range: Preset range (today, week, month) - mutually exclusive with start/end
    - start: Custom start datetime (UTC) - requires end
    - end: Custom end datetime (UTC) - requires start
    
    Returns:
    - total_seconds: Total tracked time in seconds
    - by_category: List of per-category statistics
    
    Note: Week starts on Monday. Only completed sessions (with end_time) are counted.
    """
    # Calculate time range
    start_time, end_time = _get_time_range(range_type, start, end)
    
    # Query total seconds
    # Only count completed sessions (end_time is not NULL)
    total_result = db.query(
        func.coalesce(func.sum(Session.duration_seconds), 0).label("total")
    ).filter(
        Session.user_id == current_user.id,
        Session.end_time.isnot(None),  # Only completed sessions
        Session.start_time >= start_time,
        Session.start_time <= end_time
    ).first()
    
    total_seconds = int(total_result.total) if total_result else 0
    
    # Query by category with GROUP BY (including category color)
    category_results = db.query(
        Session.category_id,
        Category.name.label("category_name"),
        Category.color.label("category_color"),
        func.coalesce(func.sum(Session.duration_seconds), 0).label("seconds")
    ).outerjoin(
        Category, Session.category_id == Category.id
    ).filter(
        Session.user_id == current_user.id,
        Session.end_time.isnot(None),  # Only completed sessions
        Session.start_time >= start_time,
        Session.start_time <= end_time
    ).group_by(
        Session.category_id,
        Category.name,
        Category.color
    ).all()
    
    # Build category stats
    by_category = [
        CategoryStats(
            category_id=row.category_id,
            category_name=row.category_name,
            category_color=row.category_color,
            seconds=int(row.seconds)
        )
        for row in category_results
    ]
    
    return StatsSummary(
        total_seconds=total_seconds,
        by_category=by_category
    )
