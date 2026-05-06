"""Quick start template endpoints."""
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_current_active_user
from app.core.db import get_db
from app.models.category import Category
from app.models.quick_start_template import QuickStartTemplate
from app.models.session import Session, SessionSource
from app.models.user import User
from app.schemas.quick_start_template import (
    QuickStartStartRequest,
    QuickStartStartResponse,
    QuickStartTemplateCreate,
    QuickStartTemplateResponse,
    QuickStartTemplateUpdate,
)

router = APIRouter()


def _get_template(template_id: int, user_id: int, db: DBSession) -> QuickStartTemplate:
    template = db.query(QuickStartTemplate).filter(
        QuickStartTemplate.id == template_id,
        QuickStartTemplate.user_id == user_id,
    ).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quick start template not found",
        )
    return template


def _get_active_session(user_id: int, db: DBSession) -> Session | None:
    return db.query(Session).filter(
        Session.user_id == user_id,
        Session.end_time.is_(None),
    ).first()


def _get_session_by_client_id(user_id: int, client_generated_id: str | None, db: DBSession) -> Session | None:
    if not client_generated_id:
        return None

    return db.query(Session).filter(
        Session.user_id == user_id,
        Session.client_generated_id == client_generated_id,
    ).first()


def _ensure_timezone(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _validate_category(category_id: int, user_id: int, db: DBSession) -> Category:
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    if category.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to use this category")
    if category.is_archived:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot use archived category")
    return category


def _to_response(template: QuickStartTemplate, db: DBSession) -> QuickStartTemplateResponse:
    category = db.query(Category).filter(Category.id == template.category_id).first()
    return QuickStartTemplateResponse.model_validate({
        **template.__dict__,
        "category_name": category.name if category else None,
    })


@router.get("", response_model=List[QuickStartTemplateResponse])
def list_templates(
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    templates = db.query(QuickStartTemplate).filter(
        QuickStartTemplate.user_id == current_user.id,
        QuickStartTemplate.is_active == True,
    ).order_by(
        QuickStartTemplate.sort_order.asc(),
        QuickStartTemplate.created_at.asc(),
    ).all()
    return [_to_response(template, db) for template in templates]


@router.post("", response_model=QuickStartTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    template_data: QuickStartTemplateCreate,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    _validate_category(template_data.category_id, current_user.id, db)

    template = QuickStartTemplate(
        user_id=current_user.id,
        title=template_data.title.strip(),
        category_id=template_data.category_id,
        duration_seconds=template_data.duration_seconds,
        note_template=template_data.note_template,
        sort_order=template_data.sort_order,
        color=template_data.color,
        icon=template_data.icon,
        is_active=True,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return _to_response(template, db)


@router.patch("/{template_id}", response_model=QuickStartTemplateResponse)
def update_template(
    template_id: int,
    template_data: QuickStartTemplateUpdate,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    template = _get_template(template_id, current_user.id, db)
    update_data = template_data.model_dump(exclude_unset=True)

    if "category_id" in update_data:
        _validate_category(update_data["category_id"], current_user.id, db)

    if "title" in update_data:
        update_data["title"] = update_data["title"].strip()

    for field, value in update_data.items():
        setattr(template, field, value)

    db.commit()
    db.refresh(template)
    return _to_response(template, db)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    template = _get_template(template_id, current_user.id, db)
    db.delete(template)
    db.commit()
    return None


@router.post("/{template_id}/start", response_model=QuickStartStartResponse, status_code=status.HTTP_201_CREATED)
def start_from_template(
    template_id: int,
    start_data: QuickStartStartRequest | None = None,
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    start_data = start_data or QuickStartStartRequest()
    template = _get_template(template_id, current_user.id, db)
    if not template.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quick start template not found")

    existing_session = _get_session_by_client_id(current_user.id, start_data.client_generated_id, db)
    if existing_session:
        return QuickStartStartResponse(
            template=_to_response(template, db),
            session=existing_session,
        )

    active_session = _get_active_session(current_user.id, db)
    if active_session:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an active session. Please stop it before starting a new one.",
        )

    _validate_category(template.category_id, current_user.id, db)

    session = Session(
        user_id=current_user.id,
        category_id=template.category_id,
        start_time=_ensure_timezone(start_data.started_at) if start_data.started_at else datetime.now(timezone.utc),
        note=template.note_template,
        client_generated_id=start_data.client_generated_id,
        source=SessionSource.TIMER.value,
    )
    db.add(session)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing_session = _get_session_by_client_id(current_user.id, start_data.client_generated_id, db)
        if existing_session:
            return QuickStartStartResponse(
                template=_to_response(template, db),
                session=existing_session,
            )
        raise
    db.refresh(session)

    return QuickStartStartResponse(
        template=_to_response(template, db),
        session=session,
    )
