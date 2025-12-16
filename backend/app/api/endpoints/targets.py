"""Work Targets API Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession
from typing import List

from app.models.user import User
from app.models.work_target import WorkTarget
from app.schemas.work_target import WorkTargetCreate, WorkTargetUpdate, WorkTargetResponse
from app.api.deps import get_current_active_user
from app.core.db import get_db


router = APIRouter()


@router.post("", response_model=WorkTargetResponse, status_code=status.HTTP_201_CREATED)
def create_target(
    target_data: WorkTargetCreate,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db)
):
    """
    Create a new work target.
    
    Args:
        target_data: Target configuration
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created work target
    """
    target = WorkTarget(
        user_id=current_user.id,
        period=target_data.period,
        target_seconds=target_data.target_seconds,
        include_category_ids=target_data.include_category_ids,
        effective_from=target_data.effective_from,
        is_active=True
    )
    
    db.add(target)
    db.commit()
    db.refresh(target)
    
    return target


@router.get("", response_model=List[WorkTargetResponse])
def list_targets(
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db)
):
    """
    List all work targets for the current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of work targets
    """
    targets = db.query(WorkTarget).filter(
        WorkTarget.user_id == current_user.id
    ).order_by(WorkTarget.created_at.desc()).all()
    
    return targets


@router.patch("/{target_id}", response_model=WorkTargetResponse)
def update_target(
    target_id: int,
    update_data: WorkTargetUpdate,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db)
):
    """
    Update a work target (modify target or activate/deactivate).
    
    Args:
        target_id: Target ID
        update_data: Update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated work target
        
    Raises:
        HTTPException: If target not found or not owned by user
    """
    target = db.query(WorkTarget).filter(
        WorkTarget.id == target_id,
        WorkTarget.user_id == current_user.id
    ).first()
    
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work target not found"
        )
    
    # Update fields
    if update_data.target_seconds is not None:
        target.target_seconds = update_data.target_seconds
    
    if update_data.include_category_ids is not None:
        target.include_category_ids = update_data.include_category_ids
    
    if update_data.is_active is not None:
        target.is_active = update_data.is_active
    
    db.commit()
    db.refresh(target)
    
    return target
