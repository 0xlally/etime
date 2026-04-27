"""Session Schemas (Pydantic Models)"""
from pydantic import BaseModel, Field, ConfigDict, model_validator
from datetime import date, datetime
from typing import Optional
from app.models.session import SessionSource


# Request Schemas
class SessionStart(BaseModel):
    """Start a new timer session"""
    category_id: Optional[int] = None
    note: Optional[str] = Field(None, max_length=500)


class SessionStop(BaseModel):
    """Stop current timer session"""
    note: Optional[str] = Field(None, max_length=500)
    multiplier: Optional[float] = Field(None, ge=0, le=10, description="Efficiency multiplier applied to duration")


class SessionManual(BaseModel):
    """Manually create a completed session"""
    category_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    entry_date: Optional[date] = None
    hours: Optional[int] = Field(None, ge=0, le=24)
    minutes: Optional[int] = Field(None, ge=0, le=59)
    note: Optional[str] = Field(None, max_length=500)
    multiplier: Optional[float] = Field(None, ge=0, le=10, description="Efficiency multiplier applied to duration")

    @model_validator(mode="after")
    def validate_manual_time(self):
        has_range = self.start_time is not None or self.end_time is not None
        has_duration = self.entry_date is not None or self.hours is not None or self.minutes is not None

        if has_range and has_duration:
            raise ValueError("Provide either start_time/end_time or entry_date/hours/minutes")

        if has_range:
            if self.start_time is None or self.end_time is None:
                raise ValueError("Both start_time and end_time are required")
            if self.end_time <= self.start_time:
                raise ValueError("end_time must be after start_time")
            return self

        if self.entry_date is None:
            raise ValueError("entry_date is required when start_time/end_time are not provided")

        hours = self.hours or 0
        minutes = self.minutes or 0
        if hours == 0 and minutes == 0:
            raise ValueError("Manual duration must be greater than zero")

        return self


class SessionAdjustMultiplier(BaseModel):
    """Adjust multiplier for an existing completed session"""
    multiplier: float = Field(..., ge=0, le=10, description="Efficiency multiplier applied to duration")


# Response Schemas
class SessionResponse(BaseModel):
    """Session response model"""
    id: int
    user_id: int
    category_id: Optional[int] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    effective_seconds: Optional[int] = None
    effectiveness_multiplier: Optional[float] = None
    note: Optional[str] = None
    source: SessionSource
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ActiveSessionResponse(BaseModel):
    """Active (ongoing) session response"""
    id: int
    user_id: int
    category_id: Optional[int] = None
    start_time: datetime
    note: Optional[str] = None
    elapsed_seconds: int  # Calculated from start_time to now
    
    model_config = ConfigDict(from_attributes=True)
