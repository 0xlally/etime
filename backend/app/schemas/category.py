"""Category Schemas (Pydantic Models)"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Optional


# Request Schemas
class CategoryCreate(BaseModel):
    """Category creation request"""
    name: str = Field(..., min_length=1, max_length=100)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')


class CategoryUpdate(BaseModel):
    """Category update request"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    is_archived: Optional[bool] = None


class CategoryReorder(BaseModel):
    """Complete ordering of the current user's active categories."""
    category_ids: List[int] = Field(..., min_length=1)


# Response Schemas
class CategoryResponse(BaseModel):
    """Category response model"""
    id: int
    user_id: int
    name: str
    color: Optional[str] = None
    is_archived: bool
    sort_order: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
