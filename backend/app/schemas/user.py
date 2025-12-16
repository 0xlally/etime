"""User Schemas (Pydantic Models)"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.user import UserRole


# Request Schemas
class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """User login request"""
    username: str  # Can be username or email
    password: str


class TokenRefresh(BaseModel):
    """Token refresh request"""
    refresh_token: str


# Response Schemas
class UserResponse(BaseModel):
    """User response model"""
    id: int
    email: str
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data"""
    user_id: Optional[int] = None
    role: Optional[str] = None
