"""Session Schemas (Pydantic Models)"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
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


class SessionManual(BaseModel):
    """Manually create a completed session"""
    category_id: Optional[int] = None
    start_time: datetime
    end_time: datetime
    note: Optional[str] = Field(None, max_length=500)
    
    @field_validator('end_time')
    @classmethod
    def validate_end_after_start(cls, v, info):
        """Ensure end_time is after start_time"""
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('end_time must be after start_time')
        return v


# Response Schemas
class SessionResponse(BaseModel):
    """Session response model"""
    id: int
    user_id: int
    category_id: Optional[int] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
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
