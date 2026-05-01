import os
from datetime import datetime, timezone

from fastapi.testclient import TestClient

os.environ.setdefault("OPENROUTER_API_KEY", "test-key")

from app.main import app
from app.scraper import ScraperError
from app.summary_models import SummarizationResult, TokenUsage


client = TestClient(app)


def build_summary_result() -> SummarizationResult:
    return SummarizationResult(
        summary="Example summary",
        model="openai/gpt-4o-mini",
        token_usage=TokenUsage(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
        ),
    )


def test_root_serves_frontend():
    response = client.get("/")

    assert response.status_code == 200
    assert "Web Scraper Studio" in response.text
    assert "text/html" in response.headers["content-type"]


def test_scrape_endpoint_returns_scraped_data(monkeypatch):
    created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)

    async def fake_scrape_website(url):
        return {
            "url": url,
            "status_code": 200,
            "status": "crawling",
            "created_at": created_at,
            "completed_at": datetime(2026, 1, 1, 0, 0, 5, tzinfo=timezone.utc),
            "content_length": 100,
            "title": "Example Domain",
            "meta_description": "Example description",
            "links": ["https://iana.org/domains/example"],
            "images": [],
            "headings": ["Example Domain"],
        }

    def fake_generate_short_code(url):
        return "abc123"

    monkeypatch.setattr("app.main.get_cached_result", lambda url: None)
    monkeypatch.setattr("app.main.set_cached_result", lambda url, result: None)
    monkeypatch.setattr("app.main.scrape_website", fake_scrape_website)
    monkeypatch.setattr("app.main.generate_short_code", fake_generate_short_code)

    response = client.post("/scrape", json={"url": "https://example.com"})

    assert response.status_code == 200
    assert response.json() == {
        "short_code": "abc123",
        "original_url": "https://example.com/",
        "clicks": 0,
        "created_at": "2026-01-01T00:00:00Z",
        "data": {
            "url": "https://example.com/",
            "status_code": 200,
            "status": "crawling",
            "created_at": "2026-01-01T00:00:00Z",
            "completed_at": "2026-01-01T00:00:05Z",
            "content_length": 100,
            "title": "Example Domain",
            "meta_description": "Example description",
            "links": ["https://iana.org/domains/example"],
            "images": [],
            "headings": ["Example Domain"],
        },
    }


def test_scrape_endpoint_increments_clicks_for_cached_result(monkeypatch):
    cached_result = {
        "short_code": "abc123",
        "original_url": "https://example.com/",
        "clicks": 0,
        "created_at": "2026-01-01T00:00:00Z",
        "data": {
            "url": "https://example.com",
            "status_code": 200,
            "status": "crawling",
            "created_at": "2026-01-01T00:00:00Z",
            "completed_at": "2026-01-01T00:00:05Z",
            "content_length": 100,
            "title": "Example Domain",
            "meta_description": "Example description",
            "links": ["https://iana.org/domains/example"],
            "images": [],
            "headings": ["Example Domain"],
        },
    }

    def fake_get_cached_result(url):
        assert url == "https://example.com/"
        return cached_result

    def fake_increment_result_clicks(url):
        assert url == "https://example.com/"
        return {
            **cached_result,
            "clicks": 1,
        }

    monkeypatch.setattr("app.main.get_cached_result", fake_get_cached_result)
    monkeypatch.setattr("app.main.increment_result_clicks", fake_increment_result_clicks)

    response = client.post("/scrape", json={"url": "https://example.com"})

    assert response.status_code == 200
    assert response.json()["clicks"] == 1


def test_scrape_endpoint_returns_400_for_scraper_error(monkeypatch):
    async def fake_scrape_website(url):
        raise ScraperError("Only HTTPS URLs are allowed")

    monkeypatch.setattr("app.main.scrape_website", fake_scrape_website)

    response = client.post("/scrape", json={"url": "http://example.com"})

    assert response.status_code == 400
    assert response.json() == {"detail": "Only HTTPS URLs are allowed"}


def test_scrape_markdown_returns_cached_markdown_without_scraping(monkeypatch):
    def fake_get_cached_markdown(url):
        assert url == "https://example.com/"
        return "# Cached markdown"

    async def fake_scrape_website_as_markdown(url):
        raise AssertionError("scrape_website_as_markdown should not be called on cache hit")

    monkeypatch.setattr("app.main.get_cached_markdown", fake_get_cached_markdown)
    monkeypatch.setattr("app.main.scrape_website_as_markdown", fake_scrape_website_as_markdown)
    monkeypatch.setattr("app.main.generate_short_code", lambda url: "abc123")

    response = client.post("/scrape/markdown", json={"url": "https://example.com"})

    assert response.status_code == 200
    assert response.text == "# Cached markdown"
    assert response.headers["content-type"].startswith("text/markdown")
    assert response.headers["content-disposition"] == 'attachment; filename="abc123.md"'


def test_scrape_markdown_stores_markdown_after_scrape(monkeypatch):
    calls: list[tuple[str, str]] = []

    def fake_get_cached_markdown(url):
        assert url == "https://example.com/"
        return None

    async def fake_scrape_website_as_markdown(url):
        assert url == "https://example.com/"
        return "# Fresh markdown"

    def fake_set_cached_markdown(url, markdown_content):
        calls.append((url, markdown_content))

    monkeypatch.setattr("app.main.get_cached_markdown", fake_get_cached_markdown)
    monkeypatch.setattr("app.main.scrape_website_as_markdown", fake_scrape_website_as_markdown)
    monkeypatch.setattr("app.main.set_cached_markdown", fake_set_cached_markdown)
    monkeypatch.setattr("app.main.generate_short_code", lambda url: "abc123")

    response = client.post("/scrape/markdown", json={"url": "https://example.com"})

    assert response.status_code == 200
    assert response.text == "# Fresh markdown"
    assert calls == [("https://example.com/", "# Fresh markdown")]


def test_summarize_returns_cached_summary_without_calling_summariser(monkeypatch):
    cached_summary = build_summary_result()

    def fake_get_cached_summary(url, summary_type):
        assert url == "https://example.com/"
        assert summary_type == "brief"
        return cached_summary

    async def fake_summarise_markdown(content, summary_type):
        raise AssertionError("summarise_markdown should not be called on cache hit")

    monkeypatch.setattr("app.main.get_cached_summary", fake_get_cached_summary)
    monkeypatch.setattr("app.main.summarise_markdown", fake_summarise_markdown)

    response = client.post("/summarize", json={"url": "https://example.com", "max_length": "brief"})

    assert response.status_code == 200
    assert response.json() == {
        "summary": "Example summary",
        "model": "openai/gpt-4o-mini",
        "token_usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
        },
    }


def test_summarize_stores_summary_after_generation(monkeypatch):
    calls: list[tuple[str, str]] = []
    summary_cache_calls: list[tuple[str, str, SummarizationResult]] = []
    summary_result = build_summary_result()

    def fake_get_cached_summary(url, summary_type):
        assert url == "https://example.com/"
        assert summary_type == "detailed"
        return None

    def fake_get_cached_markdown(url):
        assert url == "https://example.com/"
        return None

    async def fake_scrape_website_as_markdown(url):
        assert url == "https://example.com/"
        return "# Fresh markdown"

    def fake_set_cached_markdown(url, markdown_content):
        calls.append((url, markdown_content))

    async def fake_summarise_markdown(content, summary_type):
        assert content == "# Fresh markdown"
        assert summary_type == "detailed"
        return summary_result

    def fake_set_cached_summary(url, summary_type, result):
        summary_cache_calls.append((url, summary_type, result))

    monkeypatch.setattr("app.main.get_cached_summary", fake_get_cached_summary)
    monkeypatch.setattr("app.main.get_cached_markdown", fake_get_cached_markdown)
    monkeypatch.setattr("app.main.scrape_website_as_markdown", fake_scrape_website_as_markdown)
    monkeypatch.setattr("app.main.set_cached_markdown", fake_set_cached_markdown)
    monkeypatch.setattr("app.main.summarise_markdown", fake_summarise_markdown)
    monkeypatch.setattr("app.main.set_cached_summary", fake_set_cached_summary)

    response = client.post("/summarize", json={"url": "https://example.com", "max_length": "detailed"})

    assert response.status_code == 200
    assert response.json() == {
        "summary": "Example summary",
        "model": "openai/gpt-4o-mini",
        "token_usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
        },
    }
    assert calls == [("https://example.com/", "# Fresh markdown")]
    assert summary_cache_calls == [("https://example.com/", "detailed", summary_result)]
