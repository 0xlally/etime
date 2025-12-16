"""Work Evaluations API Endpoints"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session as DBSession
from datetime import datetime, date as DateType
from typing import List, Optional

from app.models.user import User
from app.models.work_evaluation import WorkEvaluation
from app.schemas.work_target import WorkEvaluationResponse
from app.api.deps import get_current_active_user
from app.core.db import get_db


router = APIRouter()


@router.get("", response_model=List[WorkEvaluationResponse])
def list_evaluations(
    start: Optional[DateType] = Query(None, description="Start date (YYYY-MM-DD)"),
    end: Optional[DateType] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db)
):
    """
    List work evaluations for the current user.
    
    Query parameters:
    - start: Filter evaluations from this date
    - end: Filter evaluations to this date
    
    Args:
        start: Optional start date filter
        end: Optional end date filter
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of work evaluations
    """
    query = db.query(WorkEvaluation).filter(
        WorkEvaluation.user_id == current_user.id
    )
    
    # Apply date filters
    if start:
        query = query.filter(func.date(WorkEvaluation.period_start) >= start)
    
    if end:
        query = query.filter(func.date(WorkEvaluation.period_end) <= end)
    
    evaluations = query.order_by(WorkEvaluation.created_at.desc()).all()
    
    return evaluations
