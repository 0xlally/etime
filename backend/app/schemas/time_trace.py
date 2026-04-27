"""Time trace schemas."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class TimeTraceCreate(BaseModel):
    """Create a timestamped note."""
    content: str = Field(..., min_length=1, max_length=2000)


class TimeTraceResponse(BaseModel):
    """Timestamped note response."""
    id: int
    user_id: int
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
