from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, HttpUrl


class TargetCreate(BaseModel):
    url: HttpUrl
    method: str = "GET"
    expected_status: int = 200
    interval_seconds: int = 30
    timeout: float = 5.0


class TargetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    url: str
    method: str
    expected_status: int
    interval_seconds: int
    timeout: float
    is_active: bool
    created_at: datetime


class TargetStats(BaseModel):
    uptime_percent: float
    avg_latency_ms: float
    total_checks: int
    total_failures: int
