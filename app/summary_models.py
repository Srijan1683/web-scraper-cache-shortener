from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, field_validator


class SummarizationRequest(BaseModel):
    content: str
    max_length: Literal["brief", "detailed"] = "brief"
    
    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Content cannot be empty")
        return cleaned


class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class SummarizationResult(BaseModel):
    summary: str
    model: str
    token_usage: TokenUsage
