from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class QueryMetricCreate(BaseModel):
    provider: str
    model: str
    ttft_ms: float
    total_latency_ms: float
    status: str
    error_message: Optional[str] = None

class QueryMetricOut(QueryMetricCreate):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True
