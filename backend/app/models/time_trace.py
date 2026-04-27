"""Time trace model - timestamped user notes."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.sql import func
from app.core.db import Base


class TimeTrace(Base):
    """A timestamped note left by a user."""
    __tablename__ = "time_traces"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f"<TimeTrace(id={self.id}, user_id={self.user_id})>"
