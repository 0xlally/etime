"""Share card API endpoints."""
from datetime import datetime, time as TimeType, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_current_active_user
from app.api.endpoints.stats import _get_time_range
from app.core.db import get_db
from app.models.category import Category
from app.models.session import Session
from app.models.user import User
from app.models.work_target import TargetPeriod, WorkTarget
from app.schemas.share import (
    ShareCategoryStats,
    ShareHeatmapDay,
    ShareRange,
    ShareSummary,
    ShareTargetCompletion,
    ShareTargetItem,
)


router = APIRouter()


def _effective_seconds_sum():
    return func.coalesce(
        func.sum(func.coalesce(Session.effective_seconds, Session.duration_seconds)),
        0,
    )


def _date_label(value) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _sum_target_seconds(
    target: WorkTarget,
    start_time: datetime,
    end_time: datetime,
    db: DBSession,
) -> int:
    query = db.query(_effective_seconds_sum().label("seconds")).filter(
        Session.user_id == target.user_id,
        Session.end_time.isnot(None),
        Session.start_time >= start_time,
        Session.start_time <= end_time,
    )

    if target.include_category_ids:
        query = query.filter(Session.category_id.in_(target.include_category_ids))

    result = query.first()
    return int(result.seconds) if result else 0


def _target_periods_for_range(range_type: ShareRange) -> list[str]:
    if range_type == "today":
        return [TargetPeriod.DAILY.value, TargetPeriod.TOMORROW.value]
    if range_type == "week":
        return [TargetPeriod.WEEKLY.value]
    return [TargetPeriod.MONTHLY.value]


def _target_completion(
    user_id: int,
    range_type: ShareRange,
    start_time: datetime,
    end_time: datetime,
    db: DBSession,
) -> ShareTargetCompletion:
    targets = db.query(WorkTarget).filter(
        WorkTarget.user_id == user_id,
        WorkTarget.is_active == True,
        WorkTarget.period.in_(_target_periods_for_range(range_type)),
        WorkTarget.effective_from <= end_time,
    ).order_by(WorkTarget.created_at.asc(), WorkTarget.id.asc()).all()

    items: list[ShareTargetItem] = []
    for target in targets:
        if target.period == TargetPeriod.TOMORROW.value:
            effective = target.effective_from
            if effective.tzinfo is None:
                effective = effective.replace(tzinfo=timezone.utc)
            if effective.date() != start_time.date():
                continue

        actual_seconds = _sum_target_seconds(target, start_time, end_time, db)
        progress_ratio = min(1.0, actual_seconds / target.target_seconds) if target.target_seconds else 0.0
        items.append(ShareTargetItem(
            target_id=target.id,
            period=target.period,
            actual_seconds=actual_seconds,
            target_seconds=target.target_seconds,
            progress_ratio=progress_ratio,
            is_completed=actual_seconds >= target.target_seconds,
        ))

    total_count = len(items)
    completed_count = sum(1 for item in items if item.is_completed)
    if total_count == 0:
        status = "no_target"
    elif completed_count == total_count:
        status = "completed"
    else:
        status = "in_progress"

    return ShareTargetCompletion(
        total_count=total_count,
        completed_count=completed_count,
        status=status,
        items=items,
    )


def _streak_days(user_id: int, db: DBSession, as_of: Optional[datetime] = None) -> int:
    today = (as_of or datetime.now(timezone.utc)).date()
    start_date = today - timedelta(days=365)
    start_time = datetime.combine(start_date, TimeType.min).replace(tzinfo=timezone.utc)
    end_time = datetime.combine(today, TimeType.max).replace(tzinfo=timezone.utc)

    rows = db.query(func.date(Session.start_time).label("date")).filter(
        Session.user_id == user_id,
        Session.end_time.isnot(None),
        Session.start_time >= start_time,
        Session.start_time <= end_time,
    ).group_by(func.date(Session.start_time)).all()

    active_dates = {_date_label(row.date) for row in rows}
    streak = 0
    cursor = today
    while cursor.isoformat() in active_dates:
        streak += 1
        cursor -= timedelta(days=1)

    return streak


def _heatmap_preview(
    user_id: int,
    range_type: ShareRange,
    start_time: datetime,
    end_time: datetime,
    db: DBSession,
) -> list[ShareHeatmapDay]:
    if range_type == "today":
        start_date = start_time.date() - timedelta(days=13)
        end_date = start_time.date()
    else:
        start_date = start_time.date()
        end_date = end_time.date()

    preview_start = datetime.combine(start_date, TimeType.min).replace(tzinfo=timezone.utc)
    preview_end = datetime.combine(end_date, TimeType.max).replace(tzinfo=timezone.utc)

    rows = db.query(
        func.date(Session.start_time).label("date"),
        _effective_seconds_sum().label("seconds"),
    ).filter(
        Session.user_id == user_id,
        Session.end_time.isnot(None),
        Session.start_time >= preview_start,
        Session.start_time <= preview_end,
    ).group_by(func.date(Session.start_time)).all()

    totals_by_date = {_date_label(row.date): int(row.seconds) for row in rows}
    days: list[ShareHeatmapDay] = []
    cursor = start_date
    while cursor <= end_date:
        label = cursor.isoformat()
        days.append(ShareHeatmapDay(date=label, total_seconds=totals_by_date.get(label, 0)))
        cursor += timedelta(days=1)

    return days


@router.get("/summary", response_model=ShareSummary)
def get_share_summary(
    range_type: ShareRange = Query(..., alias="range", description="Preset range: today, week, or month"),
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    """Get the current user's share card summary."""
    start_time, end_time = _get_time_range(range_type, None, None)

    total_result = db.query(_effective_seconds_sum().label("total")).filter(
        Session.user_id == current_user.id,
        Session.end_time.isnot(None),
        Session.start_time >= start_time,
        Session.start_time <= end_time,
    ).first()
    total_seconds = int(total_result.total) if total_result else 0

    rows = db.query(
        Session.category_id,
        Category.name.label("category_name"),
        Category.color.label("category_color"),
        _effective_seconds_sum().label("seconds"),
    ).outerjoin(
        Category,
        and_(
            Session.category_id == Category.id,
            Category.user_id == current_user.id,
        ),
    ).filter(
        Session.user_id == current_user.id,
        Session.end_time.isnot(None),
        Session.start_time >= start_time,
        Session.start_time <= end_time,
    ).group_by(
        Session.category_id,
        Category.name,
        Category.color,
    ).all()

    by_category = [
        ShareCategoryStats(
            category_id=row.category_id,
            category_name=row.category_name,
            category_color=row.category_color,
            seconds=int(row.seconds),
            percent=(int(row.seconds) / total_seconds) if total_seconds else 0.0,
        )
        for row in sorted(rows, key=lambda item: int(item.seconds), reverse=True)
    ]

    generated_at = datetime.now(timezone.utc)
    return ShareSummary(
        range=range_type,
        start=start_time,
        end=end_time,
        total_seconds=total_seconds,
        by_category=by_category,
        target_completion=_target_completion(current_user.id, range_type, start_time, end_time, db),
        streak_days=_streak_days(current_user.id, db, generated_at),
        heatmap_preview=_heatmap_preview(current_user.id, range_type, start_time, end_time, db),
        generated_at=generated_at,
    )
