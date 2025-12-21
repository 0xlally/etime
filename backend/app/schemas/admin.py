"""Admin API Schemas"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


# User Management Schemas
class UserUpdateByAdmin(BaseModel):
    """Admin schema for updating user attributes"""
    is_active: Optional[bool] = None
    role: Optional[str] = Field(None, pattern="^(USER|ADMIN)$")


class UserListResponse(BaseModel):
    """Response schema for user list"""
    id: int
    email: str
    username: str
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PaginatedUsersResponse(BaseModel):
    """Paginated user list response"""
    total: int
    page: int
    page_size: int
    users: list[UserListResponse]


# Session Management Schemas
class SessionListItemResponse(BaseModel):
    """Response schema for session list item"""
    id: int
    user_id: int
    username: str | None = None
    category_id: Optional[int] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    note: Optional[str] = None
    source: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaginatedSessionsResponse(BaseModel):
    """Paginated session list response"""
    total: int
    page: int
    page_size: int
    sessions: list[SessionListItemResponse]


# Audit Log Schemas
class AuditLogResponse(BaseModel):
    """Response schema for audit log"""
    id: int
    admin_user_id: int
    action: str
    target_type: str
    target_id: int
    detail_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
