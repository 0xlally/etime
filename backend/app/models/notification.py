"""Notification Model - User notifications"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.core.db import Base


class Notification(Base):
    """Notification model - user notifications"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Notification content
    type = Column(String(50), nullable=False)  # e.g., "target_missed", "target_met"
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)  # NULL means unread
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.type}, read={self.read_at is not None})>"
