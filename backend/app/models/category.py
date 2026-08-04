"""Category Model"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.db import Base


class Category(Base):
    """Category database model - user's task categories"""
    __tablename__ = "categories"
    __table_args__ = (
        Index("ix_categories_user_sort", "user_id", "sort_order"),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    color = Column(String(7), nullable=True)  # Hex color code, e.g., #FF5733
    is_archived = Column(Boolean, default=False, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship
    # user = relationship("User", back_populates="categories")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name}, user_id={self.user_id})>"
