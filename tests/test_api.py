from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.scraper import ScraperError


client = TestClient(app)


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
        assert url == "https://example.com"
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
        assert url == "https://example.com"
        return None

    async def fake_scrape_website_as_markdown(url):
        assert url == "https://example.com"
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
    assert calls == [("https://example.com", "# Fresh markdown")]
