"""Stats Schemas - Request/Response models for statistics"""
from pydantic import BaseModel
from typing import List


class CategoryStats(BaseModel):
    """Statistics for a single category"""
    category_id: int | None
    category_name: str | None
    category_color: str | None = None
    seconds: int
    
    model_config = {"from_attributes": True}


class StatsSummary(BaseModel):
    """Overall statistics summary"""
    total_seconds: int
    by_category: List[CategoryStats]
    
    model_config = {"from_attributes": True}
