"""Review endpoints - daily and weekly retrospectives."""
from datetime import date as DateType
from datetime import datetime, time as TimeType, timedelta, timezone
from typing import Iterable, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session as DBSession

from app.api.deps import get_current_active_user
from app.core.db import get_db
from app.models.category import Category
from app.models.session import Session
from app.models.time_trace import TimeTrace
from app.models.user import User
from app.models.work_evaluation import EvaluationStatus, WorkEvaluation
from app.models.work_target import TargetPeriod, WorkTarget
from app.schemas.review import (
    DailyReviewResponse,
    ReviewCategoryItem,
    ReviewDayTotal,
    ReviewEvaluationItem,
    ReviewTargetSummary,
    WeeklyReviewResponse,
)


router = APIRouter()


def _date_bounds(value: DateType) -> tuple[datetime, datetime]:
    start = datetime.combine(value, TimeType.min).replace(tzinfo=timezone.utc)
    end = datetime.combine(value, TimeType.max).replace(tzinfo=timezone.utc)
    return start, end


def _week_bounds(value: DateType) -> tuple[DateType, DateType, datetime, datetime]:
    start_date = value - timedelta(days=value.weekday())
    end_date = start_date + timedelta(days=6)
    start_dt, _ = _date_bounds(start_date)
    _, end_dt = _date_bounds(end_date)
    return start_date, end_date, start_dt, end_dt


def _format_seconds(seconds: int) -> str:
    total = max(0, int(seconds))
    hours = total // 3600
    minutes = (total % 3600) // 60
    if hours == 0:
        return f"{minutes} 分钟"
    if minutes == 0:
        return f"{hours} 小时"
    return f"{hours} 小时 {minutes} 分钟"


def _category_totals(
    user_id: int,
    start_dt: datetime,
    end_dt: datetime,
    db: DBSession,
) -> List[ReviewCategoryItem]:
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

    return [
        ReviewCategoryItem(
            category_id=row.category_id,
            category_name=row.category_name,
            category_color=row.category_color,
            seconds=int(row.seconds),
        )
        for row in rows
    ]


def _with_trends(
    current: List[ReviewCategoryItem],
    previous: List[ReviewCategoryItem],
) -> List[ReviewCategoryItem]:
    previous_by_id = {item.category_id: item.seconds for item in previous}
    return [
        item.model_copy(update={
            "trend_delta_seconds": item.seconds - previous_by_id.get(item.category_id, 0)
        })
        for item in sorted(current, key=lambda value: value.seconds, reverse=True)
    ]


def _total_seconds(items: Iterable[ReviewCategoryItem]) -> int:
    return sum(item.seconds for item in items)


def _daily_totals(
    user_id: int,
    start_date: DateType,
    end_date: DateType,
    db: DBSession,
) -> List[ReviewDayTotal]:
    start_dt, _ = _date_bounds(start_date)
    _, end_dt = _date_bounds(end_date)
    rows = db.query(
        func.date(Session.start_time).label("date"),
        func.coalesce(
            func.sum(func.coalesce(Session.effective_seconds, Session.duration_seconds)),
            0,
        ).label("seconds"),
    ).filter(
        Session.user_id == user_id,
        Session.end_time.isnot(None),
        Session.start_time >= start_dt,
        Session.start_time <= end_dt,
    ).group_by(
        func.date(Session.start_time)
    ).all()

    totals_by_date = {
        row.date.isoformat() if hasattr(row.date, "isoformat") else str(row.date): int(row.seconds)
        for row in rows
    }

    days = []
    cursor = start_date
    while cursor <= end_date:
        label = cursor.isoformat()
        days.append(ReviewDayTotal(date=label, total_seconds=totals_by_date.get(label, 0)))
        cursor += timedelta(days=1)

    return days


def _time_traces(
    user_id: int,
    start_dt: datetime,
    end_dt: datetime,
    db: DBSession,
) -> List[TimeTrace]:
    return db.query(TimeTrace).filter(
        TimeTrace.user_id == user_id,
        TimeTrace.created_at >= start_dt,
        TimeTrace.created_at <= end_dt,
    ).order_by(TimeTrace.created_at.asc(), TimeTrace.id.asc()).all()


def _evaluation_items(
    user_id: int,
    start_dt: datetime,
    end_dt: datetime,
    db: DBSession,
) -> List[ReviewEvaluationItem]:
    rows = db.query(WorkEvaluation, WorkTarget.period).join(
        WorkTarget, WorkEvaluation.target_id == WorkTarget.id
    ).filter(
        WorkEvaluation.user_id == user_id,
        WorkEvaluation.period_start >= start_dt,
        WorkEvaluation.period_start <= end_dt,
    ).order_by(
        WorkEvaluation.period_start.asc(),
        WorkEvaluation.id.asc(),
    ).all()

    return [
        ReviewEvaluationItem(
            id=evaluation.id,
            target_id=evaluation.target_id,
            period=period,
            period_start=evaluation.period_start.date().isoformat(),
            period_end=evaluation.period_end.date().isoformat(),
            actual_seconds=evaluation.actual_seconds,
            target_seconds=evaluation.target_seconds,
            status=evaluation.status,
            deficit_seconds=evaluation.deficit_seconds,
        )
        for evaluation, period in rows
    ]


def _target_actual_seconds(
    target: WorkTarget,
    start_dt: datetime,
    end_dt: datetime,
    db: DBSession,
) -> int:
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


def _active_remaining_seconds(
    user_id: int,
    start_dt: datetime,
    end_dt: datetime,
    periods: list[str],
    db: DBSession,
) -> int:
    targets = db.query(WorkTarget).filter(
        WorkTarget.user_id == user_id,
        WorkTarget.is_active == True,
        WorkTarget.period.in_(periods),
        WorkTarget.effective_from <= end_dt,
    ).all()

    remaining = 0
    for target in targets:
        if target.period == TargetPeriod.TOMORROW.value:
            effective = target.effective_from
            if effective.tzinfo is None:
                effective = effective.replace(tzinfo=timezone.utc)
            if not (start_dt.date() <= effective.date() <= end_dt.date()):
                continue

        actual = _target_actual_seconds(target, start_dt, end_dt, db)
        remaining += max(0, target.target_seconds - actual)

    return remaining


def _target_summary(
    user_id: int,
    start_dt: datetime,
    end_dt: datetime,
    active_periods: list[str],
    db: DBSession,
) -> ReviewTargetSummary:
    evaluations = _evaluation_items(user_id, start_dt, end_dt, db)
    met_count = sum(1 for item in evaluations if item.status == EvaluationStatus.MET.value)
    missed_count = sum(1 for item in evaluations if item.status == EvaluationStatus.MISSED.value)
    evaluated_remaining = sum(item.deficit_seconds for item in evaluations)
    remaining = evaluated_remaining or _active_remaining_seconds(user_id, start_dt, end_dt, active_periods, db)

    return ReviewTargetSummary(
        total_count=len(evaluations),
        met_count=met_count,
        missed_count=missed_count,
        remaining_seconds=remaining,
        evaluations=evaluations,
    )


def _daily_markdown(
    value: DateType,
    total_seconds: int,
    categories: List[ReviewCategoryItem],
    target_summary: ReviewTargetSummary,
    traces: List[TimeTrace],
) -> str:
    top = categories[0].category_name if categories else "无"
    lines = [
        f"# 日报复盘 {value.isoformat()}",
        "",
        f"- 总计：{_format_seconds(total_seconds)}",
        f"- 最多分类：{top}",
        f"- 目标：达成 {target_summary.met_count} / 未达成 {target_summary.missed_count}",
        f"- 还差：{_format_seconds(target_summary.remaining_seconds)}",
        "",
        "## 分类",
    ]
    if categories:
        lines.extend(
            f"- {item.category_name or '未分类'}：{_format_seconds(item.seconds)}"
            for item in categories
        )
    else:
        lines.append("- 暂无记录")

    lines.extend(["", "## 时痕"])
    if traces:
        lines.extend(f"- {trace.created_at.strftime('%H:%M')} {trace.content}" for trace in traces)
    else:
        lines.append("- 暂无时痕")

    return "\n".join(lines)


def _weekly_markdown(
    start_date: DateType,
    end_date: DateType,
    total_seconds: int,
    average_daily_seconds: int,
    best_day: Optional[ReviewDayTotal],
    gap_days: int,
    categories: List[ReviewCategoryItem],
    target_summary: ReviewTargetSummary,
    traces: List[TimeTrace],
) -> str:
    best_day_text = f"{best_day.date}（{_format_seconds(best_day.total_seconds)}）" if best_day else "无"
    lines = [
        f"# 周报复盘 {start_date.isoformat()} - {end_date.isoformat()}",
        "",
        f"- 本周总时长：{_format_seconds(total_seconds)}",
        f"- 平均每天：{_format_seconds(average_daily_seconds)}",
        f"- 最高效的一天：{best_day_text}",
        f"- 断档天数：{gap_days}",
        f"- 目标：达成 {target_summary.met_count} / 未达成 {target_summary.missed_count}",
        f"- 还差：{_format_seconds(target_summary.remaining_seconds)}",
        "",
        "## 分类趋势",
    ]
    if categories:
        lines.extend(
            f"- {item.category_name or '未分类'}：{_format_seconds(item.seconds)}（较上期 {item.trend_delta_seconds // 60:+d} 分钟）"
            for item in categories
        )
    else:
        lines.append("- 暂无记录")

    lines.extend(["", "## 时痕"])
    if traces:
        lines.extend(f"- {trace.created_at.strftime('%m-%d %H:%M')} {trace.content}" for trace in traces)
    else:
        lines.append("- 暂无时痕")

    return "\n".join(lines)


@router.get("/daily", response_model=DailyReviewResponse)
def get_daily_review(
    date: Optional[DateType] = Query(None, description="Review date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    """Get a daily retrospective with stats, targets, and time traces."""
    review_date = date or datetime.now(timezone.utc).date()
    start_dt, end_dt = _date_bounds(review_date)
    previous_start, previous_end = _date_bounds(review_date - timedelta(days=1))

    categories = _with_trends(
        _category_totals(current_user.id, start_dt, end_dt, db),
        _category_totals(current_user.id, previous_start, previous_end, db),
    )
    total_seconds = _total_seconds(categories)
    target_summary = _target_summary(
        current_user.id,
        start_dt,
        end_dt,
        [TargetPeriod.DAILY.value, TargetPeriod.TOMORROW.value],
        db,
    )
    traces = _time_traces(current_user.id, start_dt, end_dt, db)
    markdown = _daily_markdown(review_date, total_seconds, categories, target_summary, traces)

    return DailyReviewResponse(
        date=review_date.isoformat(),
        total_seconds=total_seconds,
        top_category=categories[0] if categories else None,
        by_category=categories,
        target_summary=target_summary,
        time_traces=traces,
        markdown=markdown,
    )


@router.get("/weekly", response_model=WeeklyReviewResponse)
def get_weekly_review(
    date: Optional[DateType] = Query(None, description="Any date in the week (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user),
    db: DBSession = Depends(get_db),
):
    """Get a weekly retrospective with trends and Markdown export."""
    anchor = date or datetime.now(timezone.utc).date()
    start_date, end_date, start_dt, end_dt = _week_bounds(anchor)
    previous_start_date = start_date - timedelta(days=7)
    previous_end_date = end_date - timedelta(days=7)
    previous_start_dt, _ = _date_bounds(previous_start_date)
    _, previous_end_dt = _date_bounds(previous_end_date)

    categories = _with_trends(
        _category_totals(current_user.id, start_dt, end_dt, db),
        _category_totals(current_user.id, previous_start_dt, previous_end_dt, db),
    )
    total_seconds = _total_seconds(categories)
    daily_totals = _daily_totals(current_user.id, start_date, end_date, db)
    best_day_candidates = [item for item in daily_totals if item.total_seconds > 0]
    best_day = max(best_day_candidates, key=lambda item: item.total_seconds) if best_day_candidates else None
    gap_days = sum(1 for item in daily_totals if item.total_seconds == 0)
    average_daily_seconds = total_seconds // 7
    target_summary = _target_summary(
        current_user.id,
        start_dt,
        end_dt,
        [TargetPeriod.WEEKLY.value],
        db,
    )
    traces = _time_traces(current_user.id, start_dt, end_dt, db)
    markdown = _weekly_markdown(
        start_date,
        end_date,
        total_seconds,
        average_daily_seconds,
        best_day,
        gap_days,
        categories,
        target_summary,
        traces,
    )

    return WeeklyReviewResponse(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        total_seconds=total_seconds,
        average_daily_seconds=average_daily_seconds,
        best_day=best_day,
        gap_days=gap_days,
        by_category=categories,
        daily_totals=daily_totals,
        target_summary=target_summary,
        time_traces=traces,
        markdown=markdown,
    )
