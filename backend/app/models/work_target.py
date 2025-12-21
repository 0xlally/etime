"""WorkTarget Model - User's work time targets"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, JSON
from sqlalchemy.sql import func
from app.core.db import Base
import enum


class TargetPeriod(str, enum.Enum):
    """Target period enumeration"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    TOMORROW = "tomorrow"


class WorkTarget(Base):
    """Work target model - user's time tracking goals"""
    __tablename__ = "work_targets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # Target configuration
    period = Column(String(20), nullable=False)  # daily/weekly/monthly - store as string
    target_seconds = Column(Integer, nullable=False)  # Target time in seconds
    include_category_ids = Column(JSON, nullable=True)  # Optional category filter: [1, 2, 3]
    
    # Validity
    effective_from = Column(DateTime(timezone=True), nullable=False)  # When target becomes active
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<WorkTarget(id={self.id}, user_id={self.user_id}, period={self.period}, target={self.target_seconds}s)>"
