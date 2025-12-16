"""WorkEvaluation Model - Target evaluation results"""
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from app.core.db import Base
import enum


class EvaluationStatus(str, enum.Enum):
    """Evaluation status enumeration"""
    MET = "met"
    MISSED = "missed"


class WorkEvaluation(Base):
    """Work evaluation model - records of target evaluation results"""
    __tablename__ = "work_evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    target_id = Column(Integer, ForeignKey("work_targets.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Evaluation period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Evaluation results
    actual_seconds = Column(Integer, nullable=False)  # Actual time worked
    target_seconds = Column(Integer, nullable=False)  # Target time (copy from target)
    status = Column(String(20), nullable=False)  # met/missed - store as string
    deficit_seconds = Column(Integer, nullable=False, default=0)  # How much short (0 if met)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<WorkEvaluation(id={self.id}, target_id={self.target_id}, status={self.status})>"
