"""Time trace endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_current_active_user
from app.core.db import get_db
from app.models.time_trace import TimeTrace
from app.models.user import User
from app.schemas.time_trace import TimeTraceCreate, TimeTraceResponse


router = APIRouter()


@router.get("", response_model=List[TimeTraceResponse])
def list_time_traces(
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    """List the current user's timestamped notes."""
    return (
        db.query(TimeTrace)
        .filter(TimeTrace.user_id == current_user.id)
        .order_by(TimeTrace.created_at.desc(), TimeTrace.id.desc())
        .limit(limit)
        .all()
    )


@router.post("", response_model=TimeTraceResponse, status_code=status.HTTP_201_CREATED)
def create_time_trace(
    payload: TimeTraceCreate,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    """Create a timestamped note for the current user."""
    content = payload.content.strip()
    if not content:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="content cannot be empty")

    entry = TimeTrace(user_id=current_user.id, content=content)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
