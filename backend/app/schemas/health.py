from pydantic import BaseModel
from typing import Optional

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: float
    environment: str
    db_connected: Optional[bool] = None
    db_name: Optional[str] = None
    db_status: Optional[str] = None
    db_ping_latency: Optional[float] = None
    db_collection_count: Optional[int] = None
