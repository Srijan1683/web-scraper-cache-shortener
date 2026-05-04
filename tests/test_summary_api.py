import os

from fastapi.testclient import TestClient

os.environ.setdefault("OPENROUTER_API_KEY", "test-key")

from app.main import app
from app.summary_models import SummarizationResult, TokenUsage


client = TestClient(app)


def build_summary_result() -> SummarizationResult:
    return SummarizationResult(
        summary="Example summary",
        model="openai/gpt-4o-mini",
        token_usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )


def test_summarize_returns_cached_summary_without_calling_summariser(monkeypatch):
    cached_summary = build_summary_result()

    monkeypatch.setattr("app.main.get_cached_summary", lambda url, summary_type: cached_summary)

    response = client.post("/summarize", json={"url": "https://example.com", "max_length": "brief"})

    assert response.status_code == 200
    assert response.json()["summary"] == "Example summary"


def test_summarize_generates_summary_and_caches_it(monkeypatch):
    cached_markdown_calls: list[tuple[str, str]] = []
    cached_summary_calls: list[tuple[str, str, SummarizationResult]] = []
    summary_result = build_summary_result()

    monkeypatch.setattr("app.main.get_cached_summary", lambda url, summary_type: None)
    monkeypatch.setattr("app.main.get_cached_markdown", lambda url: None)

    async def fake_scrape_website_as_markdown(url):
        assert url == "https://example.com/"
        return "# Fresh markdown"

    async def fake_summarise_markdown(content, summary_type):
        assert content == "# Fresh markdown"
        assert summary_type == "detailed"
        return summary_result

    monkeypatch.setattr("app.main.scrape_website_as_markdown", fake_scrape_website_as_markdown)
    monkeypatch.setattr("app.main.summarise_markdown", fake_summarise_markdown)
    monkeypatch.setattr("app.main.set_cached_markdown", lambda url, markdown: cached_markdown_calls.append((url, markdown)))
    monkeypatch.setattr(
        "app.main.set_cached_summary",
        lambda url, summary_type, result: cached_summary_calls.append((url, summary_type, result)),
    )

    response = client.post("/summarize", json={"url": "https://example.com", "max_length": "detailed"})

    assert response.status_code == 200
    assert response.json()["summary"] == "Example summary"
    assert cached_markdown_calls == [("https://example.com/", "# Fresh markdown")]
    assert len(cached_summary_calls) == 1
    assert cached_summary_calls[0][0] == "https://example.com/"
    assert cached_summary_calls[0][1] == "detailed"


def test_summarize_returns_400_for_summary_error(monkeypatch):
    monkeypatch.setattr("app.main.get_cached_summary", lambda url, summary_type: None)
    monkeypatch.setattr("app.main.get_cached_markdown", lambda url: "# markdown")

    async def fake_summarise_markdown(content, summary_type):
        raise ValueError("Summary request failed: bad provider response")

    monkeypatch.setattr("app.main.summarise_markdown", fake_summarise_markdown)

    response = client.post("/summarize", json={"url": "https://example.com", "max_length": "brief"})

    assert response.status_code == 400
    assert response.json() == {"detail": "Summary request failed: bad provider response"}
