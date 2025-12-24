"""Heatmap Schemas - Request/Response models for heatmap data"""
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class HeatmapDay(BaseModel):
    """Single day's total time for heatmap"""
    date: str  # YYYY-MM-DD format
    total_seconds: int
    
    model_config = {"from_attributes": True}


class DaySessionDetail(BaseModel):
    """Session detail for a specific day"""
    id: int
    category_id: Optional[int]
    category_name: Optional[str]
    start_time: datetime
    end_time: datetime
    duration_seconds: int
    effective_seconds: Optional[int] = None
    note: Optional[str]
    source: str
    
    model_config = {"from_attributes": True}
