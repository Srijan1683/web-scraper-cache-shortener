from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, HttpUrl

from app.summary_models import SummarizationResult


SummaryType = Literal["brief", "detailed"]
JobStatus = Literal["queued", "crawling", "summarising", "completed", "failed"]


class ErrorResponse(BaseModel):
    detail: str


class ScrapeRequest(BaseModel):
    url: HttpUrl
    summary_type: SummaryType = "brief"


class ScrapeResponse(BaseModel):
    url: str
    status_code: int
    status: Literal["queued", "crawling", "summarising", "failed"]
    created_at: datetime
    completed_at: Optional[datetime] = None
    content_length: int
    title: str = ""
    meta_description: str = ""
    links: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    headings: list[str] = Field(default_factory=list)


class ScrapeResult(BaseModel):
    short_code: str
    original_url: HttpUrl
    clicks: int = 0
    created_at: datetime
    data: ScrapeResponse


class ScrapeJobResponse(BaseModel):
    job_id: str
    original_url: HttpUrl
    summary_type: SummaryType = "brief"
    status: JobStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    short_code: Optional[str] = None
    result: Optional[ScrapeResult] = None
    summary: Optional[SummarizationResult] = None
    error: Optional[str] = None


class ShortenRequest(BaseModel):
    url: HttpUrl


class ShortenResponse(BaseModel):
    code: str
    original_url: HttpUrl
    short_url: str
    created_at: datetime


class ShortUrlStats(BaseModel):
    code: str
    original_url: HttpUrl
    clicks: int = 0
    created_at: datetime
    last_accessed_at: Optional[datetime] = None


class HealthResponse(BaseModel):
    status: Literal["ok"]
    redis: Literal["connected", "disconnected"]
