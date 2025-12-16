"""AdminAuditLog Model - Admin operation audit trail"""
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from app.core.db import Base


class AdminAuditLog(Base):
    """Admin audit log model - records all admin operations for security and compliance"""
    __tablename__ = "admin_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_user_id = Column(Integer, nullable=False, index=True)  # Admin who performed the action
    
    # Action details
    action = Column(String(100), nullable=False, index=True)  # e.g. "update_user", "delete_session"
    target_type = Column(String(50), nullable=False)  # e.g. "user", "session"
    target_id = Column(Integer, nullable=False, index=True)  # ID of the affected resource
    detail_json = Column(JSON, nullable=True)  # Additional details (e.g. changes made)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    def __repr__(self):
        return f"<AdminAuditLog(id={self.id}, admin={self.admin_user_id}, action={self.action}, target={self.target_type}:{self.target_id})>"
