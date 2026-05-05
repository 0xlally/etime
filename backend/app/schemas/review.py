"""Review schemas for daily and weekly retrospectives."""
from pydantic import BaseModel
from typing import List, Optional

from app.schemas.time_trace import TimeTraceResponse


class ReviewCategoryItem(BaseModel):
    category_id: int | None
    category_name: str | None
    category_color: str | None = None
    seconds: int
    trend_delta_seconds: int = 0


class ReviewDayTotal(BaseModel):
    date: str
    total_seconds: int


class ReviewEvaluationItem(BaseModel):
    id: int
    target_id: int
    period: str
    period_start: str
    period_end: str
    actual_seconds: int
    target_seconds: int
    status: str
    deficit_seconds: int


class ReviewTargetSummary(BaseModel):
    total_count: int
    met_count: int
    missed_count: int
    remaining_seconds: int
    evaluations: List[ReviewEvaluationItem]


class DailyReviewResponse(BaseModel):
    date: str
    total_seconds: int
    top_category: Optional[ReviewCategoryItem]
    by_category: List[ReviewCategoryItem]
    target_summary: ReviewTargetSummary
    time_traces: List[TimeTraceResponse]
    markdown: str


class WeeklyReviewResponse(BaseModel):
    start_date: str
    end_date: str
    total_seconds: int
    average_daily_seconds: int
    best_day: Optional[ReviewDayTotal]
    gap_days: int
    by_category: List[ReviewCategoryItem]
    daily_totals: List[ReviewDayTotal]
    target_summary: ReviewTargetSummary
    time_traces: List[TimeTraceResponse]
    markdown: str
