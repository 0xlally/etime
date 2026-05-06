"""Quick start template model."""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.sql import func

from app.core.db import Base


class QuickStartTemplate(Base):
    """User-defined timer shortcut template."""
    __tablename__ = "quick_start_templates"
    __table_args__ = (
        Index("ix_quick_start_templates_user_sort", "user_id", "sort_order"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(100), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)
    duration_seconds = Column(Integer, nullable=True)
    note_template = Column(String(500), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    color = Column(String(7), nullable=True)
    icon = Column(String(50), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
