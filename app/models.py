from __future__ import annotations
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    detail: str


class ScrapeRequest(BaseModel):
    url: str


class ScrapeResponse(BaseModel):
    url: str
    status_code: int
    content_length: int
    title: str = ""
    meta_description: str = ""
    links: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    headings: list[str] = Field(default_factory=list)


class ScrapeResult(BaseModel):
    short_code: str
    data: ScrapeResponse
