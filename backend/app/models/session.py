"""Session Model - Time tracking sessions"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, CheckConstraint, Index, Float
from sqlalchemy.sql import func
from app.core.db import Base
import enum


class SessionSource(str, enum.Enum):
    """Session source enumeration"""
    TIMER = "timer"
    MANUAL = "manual"


class Session(Base):
    """Session database model - user's time tracking sessions"""
    __tablename__ = "sessions"
    __table_args__ = (
        Index("ix_sessions_start_time", "start_time"),
        Index("ix_sessions_end_time", "end_time"),
        Index("ix_sessions_user_start_time", "user_id", "start_time"),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Time tracking
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)  # NULL means session is ongoing
    duration_seconds = Column(Integer, nullable=True)  # Calculated when session ends
    effectiveness_multiplier = Column(Float, nullable=True, default=1.0)
    effective_seconds = Column(Integer, nullable=True)  # duration_seconds * multiplier rounded to minute
    
    # Metadata
    note = Column(String(500), nullable=True)
    source = Column(
        Enum(SessionSource, values_callable=lambda obj: [e.value for e in obj], name="sessionsource"),
        nullable=False,
        default=SessionSource.TIMER.value,
    )
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    # user = relationship("User", back_populates="sessions")
    # category = relationship("Category", back_populates="sessions")
    
    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, start={self.start_time}, end={self.end_time})>"
