"""Evaluation Service - Target evaluation logic."""
from datetime import date as DateType
from datetime import datetime, time as TimeType, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session as DBSession

from app.models.notification import Notification
from app.models.punishment_event import PunishmentEvent
from app.models.session import Session
from app.models.work_evaluation import EvaluationStatus, WorkEvaluation
from app.models.work_target import TargetPeriod, WorkTarget


DAILY_LIKE_PERIODS = {TargetPeriod.DAILY.value, TargetPeriod.TOMORROW.value}


def _date_bounds(target_date: DateType) -> tuple[datetime, datetime]:
    period_start = datetime.combine(target_date, TimeType.min).replace(tzinfo=timezone.utc)
    period_end = datetime.combine(target_date, TimeType.max).replace(tzinfo=timezone.utc)
    return period_start, period_end


def _week_bounds(target_date: DateType) -> tuple[datetime, datetime]:
    start_date = target_date - timedelta(days=target_date.weekday())
    end_date = start_date + timedelta(days=6)
    return _date_bounds(start_date)[0], _date_bounds(end_date)[1]


def _month_bounds(target_date: DateType) -> tuple[datetime, datetime]:
    start_date = target_date.replace(day=1)
    if target_date.month == 12:
        next_month = target_date.replace(year=target_date.year + 1, month=1, day=1)
    else:
        next_month = target_date.replace(month=target_date.month + 1, day=1)
    end_date = next_month - timedelta(days=1)
    return _date_bounds(start_date)[0], _date_bounds(end_date)[1]


def _period_bounds(period: str, target_date: DateType) -> tuple[datetime, datetime]:
    if period in DAILY_LIKE_PERIODS:
        return _date_bounds(target_date)
    if period == TargetPeriod.WEEKLY.value:
        return _week_bounds(target_date)
    if period == TargetPeriod.MONTHLY.value:
        return _month_bounds(target_date)
    return _date_bounds(target_date)


def _is_last_day_of_month(target_date: DateType) -> bool:
    return (target_date + timedelta(days=1)).day == 1


def _target_effective_date(target: WorkTarget) -> DateType:
    effective = target.effective_from
    if effective.tzinfo is None:
        effective = effective.replace(tzinfo=timezone.utc)
    return effective.date()


def _should_evaluate_target(target: WorkTarget, target_date: DateType) -> bool:
    if target.period == TargetPeriod.DAILY.value:
        return True
    if target.period == TargetPeriod.TOMORROW.value:
        return _target_effective_date(target) == target_date
    if target.period == TargetPeriod.WEEKLY.value:
        return target_date.weekday() == 6
    if target.period == TargetPeriod.MONTHLY.value:
        return _is_last_day_of_month(target_date)
    return False


def _sum_target_seconds(
    target: WorkTarget,
    period_start: datetime,
    period_end: datetime,
    db: DBSession,
) -> int:
    query = db.query(
        func.coalesce(
            func.sum(func.coalesce(Session.effective_seconds, Session.duration_seconds)),
            0,
        ).label("total")
    ).filter(
        Session.user_id == target.user_id,
        Session.end_time.isnot(None),
        Session.start_time >= period_start,
        Session.start_time <= period_end,
    )

    if target.include_category_ids:
        query = query.filter(Session.category_id.in_(target.include_category_ids))

    result = query.first()
    return int(result.total) if result else 0


def _suggest_compensation_seconds(deficit_seconds: int) -> int:
    if deficit_seconds <= 0:
        return 0

    minimum = 20 * 60
    maximum = 40 * 60
    suggested = max(minimum, deficit_seconds // 2)
    return min(deficit_seconds, min(maximum, suggested))


def _open_debt_events(db: DBSession, user_id: int) -> List[PunishmentEvent]:
    events = db.query(PunishmentEvent).filter(
        PunishmentEvent.user_id == user_id,
        PunishmentEvent.rule_type == "time_debt",
    ).order_by(PunishmentEvent.created_at.asc(), PunishmentEvent.id.asc()).all()

    open_events = []
    for event in events:
        payload = event.payload_json or {}
        outstanding = int(payload.get("outstanding_seconds", payload.get("deficit_seconds", 0)) or 0)
        if payload.get("status", "open") != "paid" and outstanding > 0:
            open_events.append(event)

    return open_events


def _apply_compensation(
    db: DBSession,
    user_id: int,
    evaluation: WorkEvaluation,
    surplus_seconds: int,
) -> None:
    if surplus_seconds <= 0:
        return

    remaining = surplus_seconds
    applied_total = 0
    applied_debt_ids = []

    for debt in _open_debt_events(db, user_id):
        if remaining <= 0:
            break

        payload: Dict[str, Any] = dict(debt.payload_json or {})
        outstanding = int(payload.get("outstanding_seconds", payload.get("deficit_seconds", 0)) or 0)
        applied = min(outstanding, remaining)
        if applied <= 0:
            continue

        compensated = int(payload.get("compensated_seconds", 0) or 0) + applied
        outstanding -= applied
        payload["compensated_seconds"] = compensated
        payload["outstanding_seconds"] = outstanding
        payload["status"] = "paid" if outstanding == 0 else "partial"
        debt.payload_json = payload

        remaining -= applied
        applied_total += applied
        applied_debt_ids.append(debt.id)

    if applied_total > 0:
        db.add(PunishmentEvent(
            user_id=user_id,
            evaluation_id=evaluation.id,
            rule_type="compensation",
            payload_json={
                "applied_seconds": applied_total,
                "source_surplus_seconds": surplus_seconds,
                "debt_event_ids": applied_debt_ids,
            },
        ))


def _current_period_for_target(
    target: WorkTarget,
    as_of: datetime,
) -> Optional[tuple[datetime, datetime]]:
    current_date = as_of.date()

    if target.period == TargetPeriod.TOMORROW.value:
        plan_date = _target_effective_date(target)
        if plan_date < current_date:
            return None
        return _date_bounds(plan_date)

    period_start, period_end = _period_bounds(target.period, current_date)
    effective = target.effective_from
    if effective.tzinfo is None:
        effective = effective.replace(tzinfo=timezone.utc)
    if effective > period_end:
        return None

    return period_start, period_end


def build_target_dashboard(
    user_id: int,
    db: DBSession,
    as_of: Optional[datetime] = None,
) -> dict:
    """Build target metrics, current progress, and visual event records."""
    now = as_of or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    targets = db.query(WorkTarget).filter(
        WorkTarget.user_id == user_id,
    ).order_by(WorkTarget.created_at.desc()).all()

    metrics = []
    for target in targets:
        evaluations = db.query(WorkEvaluation).filter(
            WorkEvaluation.target_id == target.id,
        ).order_by(WorkEvaluation.period_start.asc(), WorkEvaluation.id.asc()).all()

        current_streak = 0
        for evaluation in reversed(evaluations):
            if evaluation.status == EvaluationStatus.MET.value:
                current_streak += 1
            else:
                break

        best_streak = 0
        run = 0
        for evaluation in evaluations:
            if evaluation.status == EvaluationStatus.MET.value:
                run += 1
                best_streak = max(best_streak, run)
            else:
                run = 0

        met_count = sum(1 for evaluation in evaluations if evaluation.status == EvaluationStatus.MET.value)
        total_count = len(evaluations)

        active_debt_seconds = 0
        suggested_compensation_seconds = 0
        for debt in _open_debt_events(db, user_id):
            payload = debt.payload_json or {}
            if payload.get("target_id") != target.id:
                continue
            active_debt_seconds += int(payload.get("outstanding_seconds", payload.get("deficit_seconds", 0)) or 0)
            suggested_compensation_seconds += int(payload.get("suggested_compensation_seconds", 0) or 0)

        metrics.append({
            "target_id": target.id,
            "period": target.period,
            "target_seconds": target.target_seconds,
            "current_streak": current_streak,
            "best_streak": best_streak,
            "total_evaluations": total_count,
            "met_evaluations": met_count,
            "completion_rate": (met_count / total_count) if total_count else 0.0,
            "active_debt_seconds": active_debt_seconds,
            "suggested_compensation_seconds": suggested_compensation_seconds,
        })

    progress = []
    for target in targets:
        if not target.is_active:
            continue

        bounds = _current_period_for_target(target, now)
        if bounds is None:
            continue

        period_start, period_end = bounds
        actual_end = min(period_end, now)
        actual_seconds = 0 if actual_end < period_start else _sum_target_seconds(target, period_start, actual_end, db)
        remaining_seconds = max(0, target.target_seconds - actual_seconds)
        progress.append({
            "target_id": target.id,
            "period": target.period,
            "period_start": period_start,
            "period_end": period_end,
            "actual_seconds": actual_seconds,
            "target_seconds": target.target_seconds,
            "remaining_seconds": remaining_seconds,
            "progress_ratio": min(1.0, actual_seconds / target.target_seconds) if target.target_seconds else 0.0,
        })

    events = db.query(PunishmentEvent).filter(
        PunishmentEvent.user_id == user_id,
    ).order_by(PunishmentEvent.created_at.desc(), PunishmentEvent.id.desc()).limit(50).all()

    return {
        "metrics": metrics,
        "progress": progress,
        "events": events,
    }


def evaluate_targets_for_date(
    target_date: DateType,
    db: DBSession,
    user_id: Optional[int] = None,
) -> List[WorkEvaluation]:
    """
    Evaluate active targets due on a specific date.

    Daily targets are evaluated every day, weekly targets on Sunday, monthly
    targets on the last day of the month, and tomorrow targets once on their
    effective date.
    """
    _, day_end = _date_bounds(target_date)
    query = db.query(WorkTarget).filter(
        WorkTarget.is_active == True,
        WorkTarget.period.in_([
            TargetPeriod.DAILY.value,
            TargetPeriod.WEEKLY.value,
            TargetPeriod.MONTHLY.value,
            TargetPeriod.TOMORROW.value,
        ]),
        WorkTarget.effective_from <= day_end,
    )

    if user_id is not None:
        query = query.filter(WorkTarget.user_id == user_id)

    active_targets = [
        target for target in query.all()
        if _should_evaluate_target(target, target_date)
    ]

    evaluations = []

    for target in active_targets:
        period_start, period_end = _period_bounds(target.period, target_date)

        existing = db.query(WorkEvaluation).filter(
            WorkEvaluation.target_id == target.id,
            func.date(WorkEvaluation.period_start) == period_start.date(),
        ).first()

        if existing:
            continue

        actual_seconds = _sum_target_seconds(target, period_start, period_end, db)

        if actual_seconds >= target.target_seconds:
            status = EvaluationStatus.MET.value
            deficit_seconds = 0
        else:
            status = EvaluationStatus.MISSED.value
            deficit_seconds = target.target_seconds - actual_seconds

        evaluation = WorkEvaluation(
            user_id=target.user_id,
            target_id=target.id,
            period_start=period_start,
            period_end=period_end,
            actual_seconds=actual_seconds,
            target_seconds=target.target_seconds,
            status=status,
            deficit_seconds=deficit_seconds,
        )
        db.add(evaluation)
        db.flush()

        evaluations.append(evaluation)

        if status == EvaluationStatus.MISSED.value:
            suggested_compensation = _suggest_compensation_seconds(deficit_seconds)
            db.add(Notification(
                user_id=target.user_id,
                type="target_missed",
                title=f"目标未达成 - {target.period}",
                content=(
                    f"{period_start.date().isoformat()} 至 {period_end.date().isoformat()} "
                    f"少了 {deficit_seconds} 秒，建议下个可用周期补回 {suggested_compensation} 秒。"
                ),
            ))

            db.add(PunishmentEvent(
                user_id=target.user_id,
                evaluation_id=evaluation.id,
                rule_type="time_debt",
                payload_json={
                    "target_id": target.id,
                    "period": target.period,
                    "deficit_seconds": deficit_seconds,
                    "outstanding_seconds": deficit_seconds,
                    "compensated_seconds": 0,
                    "suggested_compensation_seconds": suggested_compensation,
                    "target_seconds": target.target_seconds,
                    "actual_seconds": actual_seconds,
                    "status": "open",
                    "break_record": target.period in DAILY_LIKE_PERIODS,
                },
            ))
        else:
            surplus_seconds = max(0, actual_seconds - target.target_seconds)
            _apply_compensation(db, target.user_id, evaluation, surplus_seconds)

            db.add(Notification(
                user_id=target.user_id,
                type="target_met",
                title=f"目标已达成 - {target.period}",
                content=(
                    f"{period_start.date().isoformat()} 至 {period_end.date().isoformat()} "
                    f"完成 {actual_seconds} 秒，目标 {target.target_seconds} 秒。"
                ),
            ))

    db.commit()

    return evaluations
