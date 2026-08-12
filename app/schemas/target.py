from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class TargetCreate(BaseModel):
    url:str
    method:str
    expected_status:int=200
    interval:int=30
    timeout:float= 5.0

class TargetResponse(TargetCreate):
    id:UUID
    is_active:bool
    created_at:datetime

class TargetStats(BaseModel):
    uptime_percent:float
    avg_latency_ms:float
    total_checks:int
    total_failures:int


    
