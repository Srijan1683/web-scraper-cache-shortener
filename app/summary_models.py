from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, HttpUrl


class SummarizationRequest(BaseModel):
    url: HttpUrl
    max_length: Literal["brief", "detailed"] = "brief"


class TokenUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class SummarizationResult(BaseModel):
    summary: str
    model: str
    token_usage: TokenUsage
