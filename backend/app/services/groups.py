"""Group service helpers for membership checks and share summaries."""
from __future__ import annotations

import json
import secrets
import string
from datetime import date as DateType
from datetime import datetime, time, timedelta, timezone
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session as DBSession

from app.models.category import Category
from app.models.group import Group, GroupDailySnapshot, GroupMember, GroupMessage
from app.models.session import Session
from app.models.user import User
from app.models.work_evaluation import EvaluationStatus, WorkEvaluation
from app.models.work_target import TargetPeriod, WorkTarget


INVITE_ALPHABET = string.ascii_uppercase + string.digits


def generate_invite_code(db: DBSession) -> str:
    """Generate a non-short unique invite code."""
    for _ in range(8):
        code = "".join(secrets.choice(INVITE_ALPHABET) for _ in range(10))
        exists = db.query(Group.id).filter(Group.invite_code == code).first()
        if not exists:
            return code
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not generate invite code")


def serialize_metadata(value: Optional[dict[str, Any]]) -> Optional[str]:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def parse_metadata(value: Optional[str]) -> Optional[dict[str, Any]]:
    if not value:
        return None
    try:
        loaded = json.loads(value)
        return loaded if isinstance(loaded, dict) else None
    except json.JSONDecodeError:
        return None


def get_active_membership(group_id: int, user_id: int, db: DBSession) -> Optional[GroupMember]:
    return db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id,
        GroupMember.is_active == True,
    ).first()


def require_member(group_id: int, user_id: int, db: DBSession) -> GroupMember:
    member = get_active_membership(group_id, user_id, db)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return member


def require_admin_or_owner(group_id: int, user_id: int, db: DBSession) -> GroupMember:
    member = require_member(group_id, user_id, db)
    if member.role not in {"owner", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this group")
    return member


def get_group_for_member(group_id: int, user_id: int, db: DBSession) -> tuple[Group, GroupMember]:
    member = require_member(group_id, user_id, db)
    group = db.query(Group).filter(Group.id == group_id).first()
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return group, member


def active_member_count(group_id: int, db: DBSession) -> int:
    return db.query(func.count(GroupMember.id)).filter(
        GroupMember.group_id == group_id,
        GroupMember.is_active == True,
    ).scalar() or 0


def _day_bounds(value: DateType) -> tuple[datetime, datetime]:
    start = datetime.combine(value, time.min).replace(tzinfo=timezone.utc)
    end = datetime.combine(value, time.max).replace(tzinfo=timezone.utc)
    return start, end


def _format_seconds(seconds: int) -> str:
    total = max(0, int(seconds))
    hours = total // 3600
    minutes = (total % 3600) // 60
    if hours == 0:
        return f"{minutes}分钟"
    if minutes == 0:
        return f"{hours}小时"
    return f"{hours}小时{minutes}分钟"


def _target_actual_seconds(target: WorkTarget, start_dt: datetime, end_dt: datetime, db: DBSession) -> int:
    query = db.query(
        func.coalesce(
            func.sum(func.coalesce(Session.effective_seconds, Session.duration_seconds)),
            0,
        ).label("seconds")
    ).filter(
        Session.user_id == target.user_id,
        Session.end_time.isnot(None),
        Session.start_time >= start_dt,
        Session.start_time <= end_dt,
    )
    if target.include_category_ids:
        query = query.filter(Session.category_id.in_(target.include_category_ids))
    result = query.first()
    return int(result.seconds) if result else 0


def _today_target_counts(user_id: int, today: DateType, start_dt: datetime, end_dt: datetime, db: DBSession) -> tuple[int, int]:
    evaluated = db.query(WorkEvaluation).join(
        WorkTarget, WorkEvaluation.target_id == WorkTarget.id
    ).filter(
        WorkEvaluation.user_id == user_id,
        WorkTarget.period.in_([TargetPeriod.DAILY.value, TargetPeriod.TOMORROW.value]),
        WorkEvaluation.period_start >= start_dt,
        WorkEvaluation.period_start <= end_dt,
    ).all()
    if evaluated:
        return (
            sum(1 for item in evaluated if item.status == EvaluationStatus.MET.value),
            len(evaluated),
        )

    targets = db.query(WorkTarget).filter(
        WorkTarget.user_id == user_id,
        WorkTarget.is_active == True,
        WorkTarget.period.in_([TargetPeriod.DAILY.value, TargetPeriod.TOMORROW.value]),
        WorkTarget.effective_from <= end_dt,
    ).all()
    completed = 0
    total = 0
    for target in targets:
        if target.period == TargetPeriod.TOMORROW.value:
            effective = target.effective_from
            if effective.tzinfo is None:
                effective = effective.replace(tzinfo=timezone.utc)
            if effective.date() != today:
                continue
        total += 1
        if _target_actual_seconds(target, start_dt, end_dt, db) >= target.target_seconds:
            completed += 1
    return completed, total


def _streak_days(user_id: int, today: DateType, db: DBSession) -> int:
    streak = 0
    cursor = today
    while streak < 366:
        start_dt, end_dt = _day_bounds(cursor)
        total = db.query(
            func.coalesce(
                func.sum(func.coalesce(Session.effective_seconds, Session.duration_seconds)),
                0,
            ).label("seconds")
        ).filter(
            Session.user_id == user_id,
            Session.end_time.isnot(None),
            Session.start_time >= start_dt,
            Session.start_time <= end_dt,
        ).first()
        if not total or int(total.seconds) <= 0:
            break
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def build_today_status(user_id: int, db: DBSession, today: Optional[DateType] = None) -> tuple[str, dict[str, Any]]:
    """Aggregate a user's current-day status for group sharing."""
    value = today or datetime.now(timezone.utc).date()
    start_dt, end_dt = _day_bounds(value)

    rows = db.query(
        Session.category_id,
        Category.name.label("category_name"),
        Category.color.label("category_color"),
        func.coalesce(
            func.sum(func.coalesce(Session.effective_seconds, Session.duration_seconds)),
            0,
        ).label("seconds"),
    ).outerjoin(
        Category, Session.category_id == Category.id
    ).filter(
        Session.user_id == user_id,
        Session.end_time.isnot(None),
        Session.start_time >= start_dt,
        Session.start_time <= end_dt,
    ).group_by(
        Session.category_id,
        Category.name,
        Category.color,
    ).all()

    categories = [
        {
            "category_id": row.category_id,
            "category_name": row.category_name,
            "category_color": row.category_color,
            "seconds": int(row.seconds),
        }
        for row in rows
    ]
    total_seconds = sum(item["seconds"] for item in categories)
    top_category = max(categories, key=lambda item: item["seconds"], default=None)
    target_completed_count, target_total_count = _today_target_counts(user_id, value, start_dt, end_dt, db)
    streak_days = _streak_days(user_id, value, db)

    top_name = (top_category or {}).get("category_name") or "暂无"
    content = (
        f"今天已投入 {_format_seconds(total_seconds)}，"
        f"完成 {target_completed_count}/{target_total_count} 个目标，"
        f"最长分类：{top_name}。"
    )
    metadata = {
        "date": value.isoformat(),
        "total_seconds": total_seconds,
        "top_category": top_category,
        "target_completed_count": target_completed_count,
        "target_total_count": target_total_count,
        "streak_days": streak_days,
        "by_category": categories,
    }
    return content, metadata


def save_daily_snapshot(group_id: int, user_id: int, metadata: dict[str, Any], db: DBSession) -> None:
    snapshot_date = DateType.fromisoformat(metadata["date"])
    snapshot = db.query(GroupDailySnapshot).filter(
        GroupDailySnapshot.group_id == group_id,
        GroupDailySnapshot.user_id == user_id,
        GroupDailySnapshot.date == snapshot_date,
    ).first()
    if snapshot is None:
        snapshot = GroupDailySnapshot(group_id=group_id, user_id=user_id, date=snapshot_date)
        db.add(snapshot)
    snapshot.total_seconds = int(metadata.get("total_seconds") or 0)
    snapshot.target_completed_count = int(metadata.get("target_completed_count") or 0)
    snapshot.target_total_count = int(metadata.get("target_total_count") or 0)
    snapshot.streak_days = int(metadata.get("streak_days") or 0)


def create_group_message(
    group_id: int,
    user_id: int,
    message_type: str,
    content: str,
    metadata: Optional[dict[str, Any]],
    db: DBSession,
) -> GroupMessage:
    message = GroupMessage(
        group_id=group_id,
        user_id=user_id,
        message_type=message_type,
        content=content,
        metadata_json=serialize_metadata(metadata),
    )
    db.add(message)
    return message
