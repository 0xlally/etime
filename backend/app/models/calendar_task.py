"""Calendar task model."""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.sql import func

from app.core.db import Base


class CalendarTask(Base):
    """User-owned task that can live in a planning pool or on the calendar."""
    __tablename__ = "calendar_tasks"
    __table_args__ = (
        Index("ix_calendar_tasks_user_status", "user_id", "status"),
        Index("ix_calendar_tasks_user_scheduled_start", "user_id", "scheduled_start"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(160), nullable=False)
    description = Column(String(1000), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(20), nullable=False, default="unscheduled")
    priority = Column(String(20), nullable=False, default="medium")
    estimated_seconds = Column(Integer, nullable=True)
    scheduled_start = Column(DateTime(timezone=True), nullable=True, index=True)
    scheduled_end = Column(DateTime(timezone=True), nullable=True)
    reminder_enabled = Column(Boolean, nullable=False, default=False)
    reminder_minutes_before = Column(Integer, nullable=True)
    reminder_fired_at = Column(DateTime(timezone=True), nullable=True)
    converted_session_id = Column(Integer, ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<CalendarTask(id={self.id}, user_id={self.user_id}, status={self.status})>"
