from __future__ import annotations

import asyncio
from typing import Literal

import tiktoken

from app.config import APP_TITLE, CHUNK_TOKEN_LIMIT, DIRECT_SUMMARY_TOKEN_LIMIT, OPENROUTER_HTTP_REFERER
from app.openrouter_client import client, model_name
from app.summary_models import SummarizationResult, TokenUsage


SummaryType = Literal["brief", "detailed"]

SYSTEM_PROMPT = (
    "You are a precise summarization assistant. "
    "Summarize only the provided markdown content. "
    "Do not invent facts or add information not present in the source. "
    "Preserve important names, numbers, dates, and technical details."
)

def _tokenizer_model_name() -> str:
    return model_name.split("/", 1)[-1]


def _get_encoding():
    try:
        return tiktoken.encoding_for_model(_tokenizer_model_name())
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    encoding = _get_encoding()
    return len(encoding.encode(text))


def _user_prompt(summary_type: SummaryType) -> str:
    if summary_type == "brief":
        return (
            "Summarize the following markdown in 2 to 3 sentences. "
            "Keep it concise, factual, and easy to read."
        )

    return (
        "Summarize the following markdown in one clear paragraph. "
        "Include the main purpose, key points, and notable details. "
        "Stay faithful to the source and avoid unnecessary repetition."
    )


def _extract_text_content(content: object) -> str:
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text", "")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
        return "\n".join(parts).strip()

    return ""


def split_into_chunks(text: str, max_tokens: int = CHUNK_TOKEN_LIMIT) -> list[str]:
    encoding = _get_encoding()
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]

    if not paragraphs:
        return []

    chunks: list[str] = []
    current_parts: list[str] = []
    current_tokens = 0

    for paragraph in paragraphs:
        paragraph_tokens = len(encoding.encode(paragraph))

        if current_parts and current_tokens + paragraph_tokens > max_tokens:
            chunks.append("\n\n".join(current_parts))
            current_parts = [paragraph]
            current_tokens = paragraph_tokens
            continue

        if paragraph_tokens > max_tokens:
            if current_parts:
                chunks.append("\n\n".join(current_parts))
                current_parts = []
                current_tokens = 0

            paragraph_tokens_list = encoding.encode(paragraph)
            for start in range(0, len(paragraph_tokens_list), max_tokens):
                chunk_tokens = paragraph_tokens_list[start : start + max_tokens]
                chunks.append(encoding.decode(chunk_tokens))
            continue

        current_parts.append(paragraph)
        current_tokens += paragraph_tokens

    if current_parts:
        chunks.append("\n\n".join(current_parts))

    return chunks


async def _request_summary(markdown_text: str, summary_type: SummaryType) -> SummarizationResult:
    try:
        completion = await client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": OPENROUTER_HTTP_REFERER,
                "X-OpenRouter-Title": APP_TITLE,
            },
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        f"{_user_prompt(summary_type)}\n\n"
                        f"Markdown to summarize:\n---\n{markdown_text}\n---"
                    ),
                },
            ],
        )
    except Exception as exc:
        raise ValueError(f"Summary request failed: {exc}") from exc

    summary = _extract_text_content(completion.choices[0].message.content)
    if not summary:
        raise ValueError("The summarizer returned an empty response")

    usage = completion.usage
    prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage is not None else 0
    completion_tokens = getattr(usage, "completion_tokens", 0) if usage is not None else 0
    total_tokens = getattr(usage, "total_tokens", 0) if usage is not None else 0

    return SummarizationResult(
        summary=summary,
        model=model_name,
        token_usage=TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        ),
    )


async def summarise_chunk(chunk: str, summary_type: SummaryType = "brief") -> SummarizationResult:
    return await _request_summary(chunk, summary_type)


async def summarise_markdown(
    markdown_text: str,
    summary_type: SummaryType = "brief",
) -> SummarizationResult:
    cleaned_markdown = markdown_text.strip()
    if not cleaned_markdown:
        raise ValueError("markdown_text cannot be empty")

    token_count = count_tokens(cleaned_markdown)
    if token_count <= DIRECT_SUMMARY_TOKEN_LIMIT:
        return await _request_summary(cleaned_markdown, summary_type)

    chunks = split_into_chunks(cleaned_markdown)
    if not chunks:
        raise ValueError("Unable to split markdown content into chunks")

    chunk_results = await asyncio.gather(
        *(summarise_chunk(chunk, "brief") for chunk in chunks)
    )

    combined_chunk_summaries = "\n\n".join(
        f"Chunk {index + 1} summary:\n{result.summary}"
        for index, result in enumerate(chunk_results)
    )

    final_result = await _request_summary(combined_chunk_summaries, summary_type)

    return SummarizationResult(
        summary=final_result.summary,
        model=model_name,
        token_usage=TokenUsage(
            prompt_tokens=sum(result.token_usage.prompt_tokens for result in chunk_results)
            + final_result.token_usage.prompt_tokens,
            completion_tokens=sum(result.token_usage.completion_tokens for result in chunk_results)
            + final_result.token_usage.completion_tokens,
            total_tokens=sum(result.token_usage.total_tokens for result in chunk_results)
            + final_result.token_usage.total_tokens,
        ),
    )
