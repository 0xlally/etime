"""Category Schemas (Pydantic Models)"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


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


# Response Schemas
class CategoryResponse(BaseModel):
    """Category response model"""
    id: int
    user_id: int
    name: str
    color: Optional[str] = None
    is_archived: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
