import asyncio
import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-key")

from app.summary_models import SummarizationResult, TokenUsage
from app.summariser import count_tokens, split_into_chunks, summarise_markdown


def build_summary_result(summary: str, prompt_tokens: int, completion_tokens: int, total_tokens: int) -> SummarizationResult:
    return SummarizationResult(
        summary=summary,
        model="openai/gpt-4o-mini",
        token_usage=TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        ),
    )


def test_count_tokens_returns_positive_value():
    assert count_tokens("Hello world") > 0


def test_split_into_chunks_returns_multiple_chunks_for_large_input():
    text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."

    chunks = split_into_chunks(text, max_tokens=4)

    assert len(chunks) >= 2
    assert all(chunk.strip() for chunk in chunks)


def test_summarise_markdown_raises_error_for_empty_input():
    try:
        asyncio.run(summarise_markdown("   ", "brief"))
    except ValueError as exc:
        assert str(exc) == "markdown_text cannot be empty"
    else:
        raise AssertionError("Expected ValueError for empty markdown")


def test_summarise_markdown_uses_direct_path(monkeypatch):
    async def fake_request_summary(markdown_text, summary_type):
        assert markdown_text == "# Example Domain"
        assert summary_type == "brief"
        return build_summary_result("Direct summary", 10, 5, 15)

    monkeypatch.setattr("app.summariser.count_tokens", lambda text: 10)
    monkeypatch.setattr("app.summariser._request_summary", fake_request_summary)

    result = asyncio.run(summarise_markdown("# Example Domain", "brief"))

    assert result.summary == "Direct summary"
    assert result.token_usage.total_tokens == 15


def test_summarise_markdown_uses_chunked_path(monkeypatch):
    monkeypatch.setattr("app.summariser.count_tokens", lambda text: 999999)
    monkeypatch.setattr("app.summariser.split_into_chunks", lambda text: ["chunk one", "chunk two"])

    async def fake_summarise_chunk(chunk, summary_type="brief"):
        assert summary_type == "brief"
        return build_summary_result(
            f"summary for {chunk}",
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
        )

    async def fake_request_summary(markdown_text, summary_type):
        assert "Chunk 1 summary" in markdown_text
        assert "Chunk 2 summary" in markdown_text
        assert summary_type == "detailed"
        return build_summary_result("Combined summary", 20, 7, 27)

    monkeypatch.setattr("app.summariser.summarise_chunk", fake_summarise_chunk)
    monkeypatch.setattr("app.summariser._request_summary", fake_request_summary)

    result = asyncio.run(summarise_markdown("Very long markdown", "detailed"))

    assert result.summary == "Combined summary"
    assert result.token_usage.prompt_tokens == 40
    assert result.token_usage.completion_tokens == 17
    assert result.token_usage.total_tokens == 57
