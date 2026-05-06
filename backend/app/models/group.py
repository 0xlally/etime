"""Group models for lightweight study groups and chat."""
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from app.core.db import Base


class Group(Base):
    """A user-created study/self-discipline group."""
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    invite_code = Column(String(32), unique=True, nullable=False, index=True)
    visibility = Column(String(20), nullable=False, default="invite_code")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class GroupMember(Base):
    """Membership and role inside a group."""
    __tablename__ = "group_members"
    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_group_members_group_user"),)

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False, default="member")
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    muted_until = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)


class GroupMessage(Base):
    """Lightweight group chat message."""
    __tablename__ = "group_messages"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    message_type = Column(String(20), nullable=False, default="text")
    content = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class GroupDailySnapshot(Base):
    """Optional denormalized snapshot for future group dashboards."""
    __tablename__ = "group_daily_snapshots"
    __table_args__ = (UniqueConstraint("group_id", "user_id", "date", name="uq_group_daily_snapshots_group_user_date"),)

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    total_seconds = Column(Integer, nullable=False, default=0)
    target_completed_count = Column(Integer, nullable=False, default=0)
    target_total_count = Column(Integer, nullable=False, default=0)
    streak_days = Column(Integer, nullable=False, default=0)
