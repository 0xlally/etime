"""PunishmentEvent Model - Punishment records for missed targets"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.core.db import Base


class PunishmentEvent(Base):
    """Punishment event model - records of punishments for missed targets"""
    __tablename__ = "punishment_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    evaluation_id = Column(Integer, ForeignKey("work_evaluations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Punishment configuration
    rule_type = Column(String(50), nullable=False)  # e.g., "streak_break", "remind_only"
    payload_json = Column(JSON, nullable=True)  # Additional data for the punishment
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<PunishmentEvent(id={self.id}, rule_type={self.rule_type})>"
