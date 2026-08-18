from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CheckLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    target_id: UUID
    status_code: int | None
    response_time_ms: float | None
    is_success: bool
    error_message: str | None
    created_at: datetime
