"""Evaluation Service - Target evaluation logic"""
from sqlalchemy import func
from sqlalchemy.orm import Session as DBSession
from datetime import datetime, timezone, timedelta, date as DateType
from typing import List, Optional

from app.models.work_target import WorkTarget, TargetPeriod
from app.models.work_evaluation import WorkEvaluation, EvaluationStatus
from app.models.notification import Notification
from app.models.punishment_event import PunishmentEvent
from app.models.session import Session


def evaluate_targets_for_date(
    target_date: DateType,
    db: DBSession,
    user_id: Optional[int] = None
) -> List[WorkEvaluation]:
    """
    Evaluate all active daily targets for a specific date.
    
    For each active daily target:
    1. Calculate actual working seconds (optionally filtered by category)
    2. Compare with target_seconds
    3. Create WorkEvaluation record
    4. If missed: Create Notification and PunishmentEvent
    
    Args:
        target_date: The date to evaluate (UTC date)
        db: Database session
        user_id: Optional user_id to filter (for testing), None means all users
        
    Returns:
        List of created WorkEvaluation records
    """
    # Query active daily targets
    query = db.query(WorkTarget).filter(
        WorkTarget.is_active == True,
        WorkTarget.period == TargetPeriod.DAILY.value,  # Use .value to get string
        func.date(WorkTarget.effective_from) <= target_date
    )
    
    if user_id is not None:
        query = query.filter(WorkTarget.user_id == user_id)
    
    active_targets = query.all()
    
    evaluations = []
    
    for target in active_targets:
        # Check if evaluation already exists for this date
        existing = db.query(WorkEvaluation).filter(
            WorkEvaluation.target_id == target.id,
            func.date(WorkEvaluation.period_start) == target_date
        ).first()
        
        if existing:
            continue  # Already evaluated
        
        # Define period boundaries (00:00:00 to 23:59:59 UTC)
        period_start = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        period_end = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        # Calculate actual working seconds
        query = db.query(
            func.coalesce(func.sum(Session.duration_seconds), 0).label("total")
        ).filter(
            Session.user_id == target.user_id,
            Session.end_time.isnot(None),  # Only completed sessions
            Session.start_time >= period_start,
            Session.start_time <= period_end
        )
        
        # Filter by categories if specified
        if target.include_category_ids:
            query = query.filter(Session.category_id.in_(target.include_category_ids))
        
        result = query.first()
        actual_seconds = int(result.total) if result else 0
        
        # Determine status
        if actual_seconds >= target.target_seconds:
            status = EvaluationStatus.MET
            deficit_seconds = 0
        else:
            status = EvaluationStatus.MISSED
            deficit_seconds = target.target_seconds - actual_seconds
        
        # Create evaluation record
        evaluation = WorkEvaluation(
            user_id=target.user_id,
            target_id=target.id,
            period_start=period_start,
            period_end=period_end,
            actual_seconds=actual_seconds,
            target_seconds=target.target_seconds,
            status=status,
            deficit_seconds=deficit_seconds
        )
        db.add(evaluation)
        db.flush()  # Get evaluation.id
        
        evaluations.append(evaluation)
        
        # If missed, create notification and punishment
        if status == EvaluationStatus.MISSED:
            # Create notification
            notification = Notification(
                user_id=target.user_id,
                type="target_missed",
                title=f"Daily Target Missed - {target_date.isoformat()}",
                content=f"You missed your daily target of {target.target_seconds}s. Actual: {actual_seconds}s. Deficit: {deficit_seconds}s."
            )
            db.add(notification)
            
            # Create punishment event
            punishment = PunishmentEvent(
                user_id=target.user_id,
                evaluation_id=evaluation.id,
                rule_type="streak_break",  # Default rule
                payload_json={
                    "deficit_seconds": deficit_seconds,
                    "target_seconds": target.target_seconds,
                    "actual_seconds": actual_seconds
                }
            )
            db.add(punishment)
        else:
            # Target met - create success notification
            notification = Notification(
                user_id=target.user_id,
                type="target_met",
                title=f"Daily Target Met! - {target_date.isoformat()}",
                content=f"Great job! You met your daily target of {target.target_seconds}s with {actual_seconds}s worked."
            )
            db.add(notification)
    
    db.commit()
    
    return evaluations
