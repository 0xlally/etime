"""Quick start template schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.session import SessionResponse


class QuickStartTemplateBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    category_id: int
    duration_seconds: Optional[int] = Field(None, ge=60)
    note_template: Optional[str] = Field(None, max_length=500)
    sort_order: int = 0
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)


class QuickStartTemplateCreate(QuickStartTemplateBase):
    pass


class QuickStartTemplateUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    category_id: Optional[int] = None
    duration_seconds: Optional[int] = Field(None, ge=60)
    note_template: Optional[str] = Field(None, max_length=500)
    sort_order: Optional[int] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class QuickStartStartRequest(BaseModel):
    client_generated_id: Optional[str] = Field(None, max_length=100)
    started_at: Optional[datetime] = None


class QuickStartTemplateResponse(BaseModel):
    id: int
    user_id: int
    title: str
    category_id: int
    category_name: Optional[str] = None
    duration_seconds: Optional[int] = None
    note_template: Optional[str] = None
    sort_order: int
    color: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuickStartStartResponse(BaseModel):
    template: QuickStartTemplateResponse
    session: SessionResponse
