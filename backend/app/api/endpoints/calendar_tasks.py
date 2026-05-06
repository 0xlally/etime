"""Calendar task endpoints."""
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_current_active_user
from app.core.db import get_db
from app.models.calendar_task import CalendarTask
from app.models.category import Category
from app.models.session import Session, SessionSource
from app.models.user import User
from app.schemas.calendar_task import (
    CalendarTaskCreate,
    CalendarTaskResponse,
    CalendarTaskStatus,
    CalendarTaskUpdate,
)


router = APIRouter()


def _ensure_timezone(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _validate_category_ownership(category_id: Optional[int], user_id: int, db: DBSession) -> None:
    if category_id is None:
        return

    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    if category.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to use this category")


def _get_task(task_id: int, user_id: int, db: DBSession) -> CalendarTask:
    task = db.query(CalendarTask).filter(
        CalendarTask.id == task_id,
        CalendarTask.user_id == user_id,
    ).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar task not found")
    return task


def _task_response(task: CalendarTask, db: DBSession) -> CalendarTaskResponse:
    category_name = None
    category_color = None
    if task.category_id is not None:
        category = db.query(Category).filter(
            Category.id == task.category_id,
            Category.user_id == task.user_id,
        ).first()
        if category:
            category_name = category.name
            category_color = category.color

    return CalendarTaskResponse(
        id=task.id,
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        category_id=task.category_id,
        category_name=category_name,
        category_color=category_color,
        status=task.status,
        priority=task.priority,
        estimated_seconds=task.estimated_seconds,
        scheduled_start=task.scheduled_start,
        scheduled_end=task.scheduled_end,
        reminder_enabled=task.reminder_enabled,
        reminder_minutes_before=task.reminder_minutes_before,
        reminder_fired_at=task.reminder_fired_at,
        converted_session_id=task.converted_session_id,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def _derived_status(payload: dict, fallback: str = "unscheduled") -> str:
    if payload.get("status"):
        return payload["status"]
    if payload.get("scheduled_start") is not None and payload.get("scheduled_end") is not None:
        return "scheduled"
    return fallback


@router.get("/reminders/due", response_model=list[CalendarTaskResponse])
def get_due_reminders(
    now: Optional[datetime] = Query(None, description="Override current time for tests"),
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    """Get reminder-enabled scheduled tasks whose reminder window has arrived."""
    current_time = _ensure_timezone(now) or datetime.now(timezone.utc)
    tasks = db.query(CalendarTask).filter(
        CalendarTask.user_id == current_user.id,
        CalendarTask.status == "scheduled",
        CalendarTask.reminder_enabled == True,
        CalendarTask.reminder_fired_at.is_(None),
        CalendarTask.scheduled_start.isnot(None),
    ).order_by(CalendarTask.scheduled_start.asc(), CalendarTask.id.asc()).all()

    due = []
    for task in tasks:
        reminder_minutes = task.reminder_minutes_before if task.reminder_minutes_before is not None else 10
        reminder_time = _ensure_timezone(task.scheduled_start) - timedelta(minutes=reminder_minutes)
        if reminder_time <= current_time:
            due.append(_task_response(task, db))

    return due


@router.get("", response_model=list[CalendarTaskResponse])
def list_calendar_tasks(
    status_filter: Optional[CalendarTaskStatus] = Query(None, alias="status"),
    start: Optional[datetime] = Query(None, description="Scheduled range start"),
    end: Optional[datetime] = Query(None, description="Scheduled range end"),
    include_unscheduled: bool = Query(True),
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    """List current user's calendar tasks, optionally scoped to a scheduled range."""
    query = db.query(CalendarTask).filter(CalendarTask.user_id == current_user.id)

    if status_filter:
        query = query.filter(CalendarTask.status == status_filter)

    start_time = _ensure_timezone(start)
    end_time = _ensure_timezone(end)
    if start_time and end_time:
        scheduled_overlap = and_(
            CalendarTask.scheduled_start.isnot(None),
            CalendarTask.scheduled_end.isnot(None),
            CalendarTask.scheduled_start <= end_time,
            CalendarTask.scheduled_end >= start_time,
        )
        if include_unscheduled:
            query = query.filter(or_(
                CalendarTask.status == "unscheduled",
                scheduled_overlap,
            ))
        else:
            query = query.filter(scheduled_overlap)

    tasks = query.order_by(
        CalendarTask.scheduled_start.asc().nullsfirst(),
        CalendarTask.created_at.desc(),
        CalendarTask.id.desc(),
    ).all()
    return [_task_response(task, db) for task in tasks]


@router.post("", response_model=CalendarTaskResponse, status_code=status.HTTP_201_CREATED)
def create_calendar_task(
    task_data: CalendarTaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    """Create a calendar task in the pool or directly on the calendar."""
    payload = task_data.model_dump(exclude_unset=True)
    _validate_category_ownership(payload.get("category_id"), current_user.id, db)

    task = CalendarTask(
        user_id=current_user.id,
        title=payload["title"],
        description=payload.get("description"),
        category_id=payload.get("category_id"),
        status=_derived_status(payload),
        priority=payload.get("priority") or "medium",
        estimated_seconds=payload.get("estimated_seconds"),
        scheduled_start=_ensure_timezone(payload.get("scheduled_start")),
        scheduled_end=_ensure_timezone(payload.get("scheduled_end")),
        reminder_enabled=bool(payload.get("reminder_enabled", False)),
        reminder_minutes_before=payload.get("reminder_minutes_before"),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return _task_response(task, db)


@router.patch("/{task_id}", response_model=CalendarTaskResponse)
def update_calendar_task(
    task_id: int,
    task_data: CalendarTaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    """Update a current user's calendar task."""
    task = _get_task(task_id, current_user.id, db)
    payload = task_data.model_dump(exclude_unset=True)

    if "category_id" in payload:
        _validate_category_ownership(payload.get("category_id"), current_user.id, db)

    for field in [
        "title",
        "description",
        "category_id",
        "priority",
        "estimated_seconds",
        "reminder_enabled",
        "reminder_minutes_before",
    ]:
        if field in payload:
            setattr(task, field, payload[field])

    if "scheduled_start" in payload:
        task.scheduled_start = _ensure_timezone(payload["scheduled_start"])
    if "scheduled_end" in payload:
        task.scheduled_end = _ensure_timezone(payload["scheduled_end"])

    if "status" in payload and payload["status"] is not None:
        task.status = payload["status"]
    elif "scheduled_start" in payload or "scheduled_end" in payload:
        task.status = "scheduled" if task.scheduled_start and task.scheduled_end else "unscheduled"

    if task.status != "scheduled":
        task.reminder_fired_at = None

    db.commit()
    db.refresh(task)
    return _task_response(task, db)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_calendar_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    """Delete a current user's calendar task."""
    task = _get_task(task_id, current_user.id, db)
    db.delete(task)
    db.commit()
    return None


@router.post("/{task_id}/complete", response_model=CalendarTaskResponse)
def complete_calendar_task(
    task_id: int,
    create_session: bool = Query(False),
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    """Mark a task done and optionally convert its scheduled time into a session."""
    task = _get_task(task_id, current_user.id, db)

    if create_session and task.converted_session_id is None:
        start_time = _ensure_timezone(task.scheduled_start)
        end_time = _ensure_timezone(task.scheduled_end)
        if start_time is None or end_time is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="scheduled_start and scheduled_end are required to create a session",
            )

        duration_seconds = int((end_time - start_time).total_seconds())
        note_parts = [task.title]
        if task.description:
            note_parts.append(task.description)
        note = "\n".join(note_parts)[:500]
        session = Session(
            user_id=current_user.id,
            category_id=task.category_id,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration_seconds,
            effectiveness_multiplier=1.0,
            effective_seconds=duration_seconds,
            note=note,
            source=SessionSource.MANUAL.value,
        )
        db.add(session)
        db.flush()
        task.converted_session_id = session.id

    task.status = "done"
    task.reminder_fired_at = task.reminder_fired_at or datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    return _task_response(task, db)


@router.post("/{task_id}/reminder-fired", response_model=CalendarTaskResponse)
def mark_reminder_fired(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    """Mark a current user's task reminder as fired."""
    task = _get_task(task_id, current_user.id, db)
    task.reminder_fired_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    return _task_response(task, db)
