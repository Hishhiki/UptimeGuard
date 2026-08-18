from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    telegram_id: int
    username: str | None = None

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:UUID
    telegram_id:int
    username:str|None
    is_active:bool
    created_at: datetime

class UserStats(BaseModel):
    total_targets: int


