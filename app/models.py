from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


class ErrorResponse(BaseModel):
    detail: str


class ScrapeRequest(BaseModel):
    url: HttpUrl


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