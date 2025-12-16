"""Work Target Schemas - Request/Response models for work targets"""
from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List


class WorkTargetCreate(BaseModel):
    """Schema for creating a work target"""
    period: str  # "daily", "weekly", "monthly"
    target_seconds: int
    include_category_ids: Optional[List[int]] = None
    effective_from: datetime
    
    @field_validator("period")
    @classmethod
    def validate_period(cls, v):
        if v not in ["daily", "weekly", "monthly"]:
            raise ValueError("period must be 'daily', 'weekly', or 'monthly'")
        return v
    
    @field_validator("target_seconds")
    @classmethod
    def validate_target_seconds(cls, v):
        if v <= 0:
            raise ValueError("target_seconds must be positive")
        return v


class WorkTargetUpdate(BaseModel):
    """Schema for updating a work target"""
    target_seconds: Optional[int] = None
    include_category_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None
    
    @field_validator("target_seconds")
    @classmethod
    def validate_target_seconds(cls, v):
        if v is not None and v <= 0:
            raise ValueError("target_seconds must be positive")
        return v


class WorkTargetResponse(BaseModel):
    """Schema for work target response"""
    id: int
    user_id: int
    period: str
    target_seconds: int
    include_category_ids: Optional[List[int]]
    effective_from: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class WorkEvaluationResponse(BaseModel):
    """Schema for work evaluation response"""
    id: int
    user_id: int
    target_id: int
    period_start: datetime
    period_end: datetime
    actual_seconds: int
    target_seconds: int
    status: str  # "met" or "missed"
    deficit_seconds: int
    created_at: datetime
    
    model_config = {"from_attributes": True}


class NotificationResponse(BaseModel):
    """Schema for notification response"""
    id: int
    user_id: int
    type: str
    title: str
    content: Optional[str]
    created_at: datetime
    read_at: Optional[datetime]
    
    model_config = {"from_attributes": True}
