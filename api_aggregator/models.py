from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SourceConfig(BaseModel):
    name: str
    url: str
    params: dict = {}
    method: str = "GET"
    headers: dict = {}
    response_mapping: dict

class AppConfig(BaseModel):
    sources: list[SourceConfig]

class FetchResult(BaseModel):
    source_name: str
    success: bool
    data: Optional[dict] = None
    status_code: Optional[int] = None
    elapsed_ms: float
    error: Optional[str] = None
    retries_used: int = 0

class AggregatedReport(BaseModel):
    timestamp: datetime
    total_sources: int
    successful: int
    failed: int
    total_time_ms: float
    results: list[FetchResult]