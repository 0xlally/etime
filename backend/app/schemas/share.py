"""Share card summary schemas."""
from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel


ShareRange = Literal["today", "week", "month"]


class ShareCategoryStats(BaseModel):
    """Category contribution for a share card."""
    category_id: int | None
    category_name: str | None
    category_color: str | None = None
    seconds: int
    percent: float


class ShareTargetItem(BaseModel):
    """Single target progress item for the current share range."""
    target_id: int
    period: str
    actual_seconds: int
    target_seconds: int
    progress_ratio: float
    is_completed: bool


class ShareTargetCompletion(BaseModel):
    """Target completion rollup for a share card."""
    total_count: int
    completed_count: int
    status: Literal["no_target", "in_progress", "completed"]
    items: List[ShareTargetItem]


class ShareHeatmapDay(BaseModel):
    """Filled daily total used by the share card heatmap preview."""
    date: str
    total_seconds: int


class ShareSummary(BaseModel):
    """Summary payload used to render a share card."""
    range: ShareRange
    start: datetime
    end: datetime
    total_seconds: int
    by_category: List[ShareCategoryStats]
    target_completion: ShareTargetCompletion
    streak_days: int
    heatmap_preview: List[ShareHeatmapDay]
    generated_at: datetime
