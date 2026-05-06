"""Calendar task schemas."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


CalendarTaskStatus = Literal["unscheduled", "scheduled", "done", "cancelled"]
CalendarTaskPriority = Literal["low", "medium", "high"]


class CalendarTaskBase(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=160)
    description: Optional[str] = Field(None, max_length=1000)
    category_id: Optional[int] = None
    status: Optional[CalendarTaskStatus] = None
    priority: Optional[CalendarTaskPriority] = "medium"
    estimated_seconds: Optional[int] = Field(None, ge=60)
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    reminder_enabled: Optional[bool] = False
    reminder_minutes_before: Optional[int] = Field(None, ge=0, le=1440)

    @model_validator(mode="after")
    def validate_schedule(self):
        if self.scheduled_start is not None or self.scheduled_end is not None:
            if self.scheduled_start is None or self.scheduled_end is None:
                raise ValueError("scheduled_start and scheduled_end must be provided together")
            if self.scheduled_end <= self.scheduled_start:
                raise ValueError("scheduled_end must be after scheduled_start")

        if self.reminder_enabled and self.reminder_minutes_before is None:
            self.reminder_minutes_before = 10

        return self


class CalendarTaskCreate(CalendarTaskBase):
    title: str = Field(..., min_length=1, max_length=160)


class CalendarTaskUpdate(CalendarTaskBase):
    pass


class CalendarTaskResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str]
    category_id: Optional[int]
    category_name: Optional[str] = None
    category_color: Optional[str] = None
    status: CalendarTaskStatus
    priority: CalendarTaskPriority
    estimated_seconds: Optional[int]
    scheduled_start: Optional[datetime]
    scheduled_end: Optional[datetime]
    reminder_enabled: bool
    reminder_minutes_before: Optional[int]
    reminder_fired_at: Optional[datetime]
    converted_session_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
