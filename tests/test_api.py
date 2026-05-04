import os
from datetime import datetime, timezone

from fastapi.testclient import TestClient

os.environ.setdefault("OPENROUTER_API_KEY", "test-key")

from app.main import app
from app.models import ScrapeJobResponse, ScrapeResponse, ScrapeResult, ShortUrlStats
from app.summary_models import SummarizationResult, TokenUsage


client = TestClient(app)


def build_summary_result() -> SummarizationResult:
    return SummarizationResult(
        summary="Example summary",
        model="openai/gpt-4o-mini",
        token_usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )


def build_scrape_result(url: str = "https://example.com/") -> ScrapeResult:
    created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return ScrapeResult(
        short_code="abc123",
        original_url=url,
        clicks=0,
        created_at=created_at,
        data=ScrapeResponse(
            url=url,
            status_code=200,
            status="crawling",
            created_at=created_at,
            completed_at=datetime(2026, 1, 1, 0, 0, 5, tzinfo=timezone.utc),
            content_length=100,
            title="Example Domain",
            meta_description="Example description",
            links=["https://iana.org/domains/example"],
            images=[],
            headings=["Example Domain"],
        ),
    )


def build_job(status: str = "completed", include_summary: bool = True) -> ScrapeJobResponse:
    result = build_scrape_result()
    summary = build_summary_result() if include_summary else None
    return ScrapeJobResponse(
        job_id="job-123",
        original_url="https://example.com/",
        summary_type="brief",
        status=status,
        created_at=result.created_at,
        completed_at=result.data.completed_at if status == "completed" else None,
        short_code=result.short_code,
        result=result if status != "queued" else None,
        summary=summary,
        error="Job failed" if status == "failed" else None,
    )


def test_root_serves_frontend():
    response = client.get("/")

    assert response.status_code == 200
    assert "Web Scraper Studio" in response.text
    assert "text/html" in response.headers["content-type"]


def test_scrape_returns_cached_completed_job(monkeypatch):
    completed_job = build_job()

    monkeypatch.setattr("app.main.get_job_id_for_url", lambda url, summary_type: "job-123")
    monkeypatch.setattr("app.main.get_cached_job", lambda job_id: completed_job)

    response = client.post("/scrape", json={"url": "https://example.com", "summary_type": "brief"})

    assert response.status_code == 200
    assert response.json()["job_id"] == "job-123"
    assert response.json()["status"] == "completed"
    assert response.json()["summary"]["summary"] == "Example summary"


def test_scrape_queues_new_job_when_cache_misses(monkeypatch):
    saved_jobs: list[ScrapeJobResponse] = []
    saved_job_map: list[tuple[str, str, str]] = []

    monkeypatch.setattr("app.main.get_job_id_for_url", lambda url, summary_type: None)
    monkeypatch.setattr("app.main.get_cached_result", lambda url: None)
    monkeypatch.setattr("app.main.get_cached_summary", lambda url, summary_type: None)
    monkeypatch.setattr("app.main.set_cached_job", lambda job_id, data: saved_jobs.append(data))
    monkeypatch.setattr(
        "app.main.set_job_id_for_url",
        lambda url, summary_type, job_id: saved_job_map.append((url, summary_type, job_id)),
    )
    monkeypatch.setattr("app.main.process_scrape_job", lambda job_id, url, summary_type: None)
    monkeypatch.setattr("app.main.generate_short_code", lambda url: "abc123")

    response = client.post("/scrape", json={"url": "https://example.com", "summary_type": "detailed"})

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["summary_type"] == "detailed"
    assert body["short_code"] == "abc123"
    assert len(saved_jobs) == 1
    assert saved_job_map == [("https://example.com/", "detailed", body["job_id"])]


def test_get_scrape_job_returns_job(monkeypatch):
    monkeypatch.setattr("app.main.get_cached_job", lambda job_id: build_job(status="summarising", include_summary=False))

    response = client.get("/scrape/job-123")

    assert response.status_code == 200
    assert response.json()["job_id"] == "job-123"
    assert response.json()["status"] == "summarising"


def test_get_scrape_summary_returns_409_while_processing(monkeypatch):
    monkeypatch.setattr("app.main.get_cached_job", lambda job_id: build_job(status="summarising", include_summary=False))

    response = client.get("/scrape/job-123/summary")

    assert response.status_code == 409
    assert response.json() == {"detail": "Job still processing"}


def test_get_scrape_summary_returns_summary(monkeypatch):
    monkeypatch.setattr("app.main.get_cached_job", lambda job_id: build_job())

    response = client.get("/scrape/job-123/summary")

    assert response.status_code == 200
    assert response.json()["summary"] == "Example summary"


def test_delete_scrape_job_removes_related_cache(monkeypatch):
    deleted: list[tuple[str, str]] = []
    monkeypatch.setattr("app.main.get_cached_job", lambda job_id: build_job())
    monkeypatch.setattr("app.main.delete_cached_job", lambda job_id: deleted.append(("job", job_id)))
    monkeypatch.setattr(
        "app.main.delete_job_id_for_url",
        lambda url, summary_type: deleted.append(("map", f"{summary_type}:{url}")),
    )
    monkeypatch.setattr(
        "app.main.delete_cached_summary",
        lambda url, summary_type: deleted.append(("summary", f"{summary_type}:{url}")),
    )
    monkeypatch.setattr("app.main.delete_cached_markdown", lambda url: deleted.append(("markdown", url)))
    monkeypatch.setattr("app.main.delete_cached_result", lambda url: deleted.append(("result", url)))

    response = client.delete("/scrape/job-123")

    assert response.status_code == 204
    assert ("job", "job-123") in deleted
    assert ("result", "https://example.com/") in deleted


def test_scrape_markdown_returns_cached_markdown_without_scraping(monkeypatch):
    monkeypatch.setattr("app.main.get_cached_markdown", lambda url: "# Cached markdown")
    monkeypatch.setattr("app.main.generate_short_code", lambda url: "abc123")

    response = client.post("/scrape/markdown", json={"url": "https://example.com", "summary_type": "brief"})

    assert response.status_code == 200
    assert response.text == "# Cached markdown"
    assert response.headers["content-disposition"] == 'attachment; filename="abc123.md"'


def test_create_short_url_returns_created_response(monkeypatch):
    short_url_stats = ShortUrlStats(
        code="abc123",
        original_url="https://example.com/",
        clicks=0,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    monkeypatch.setattr("app.main.generate_short_code", lambda url: "abc123")
    monkeypatch.setattr("app.main.get_short_url", lambda code: None)
    monkeypatch.setattr("app.main.set_short_url", lambda code, data: None)
    monkeypatch.setattr("app.main.ShortUrlStats", lambda **kwargs: short_url_stats)

    response = client.post("/shorten", json={"url": "https://example.com"})

    assert response.status_code == 201
    assert response.json()["code"] == "abc123"
    assert response.json()["short_url"] == "/s/abc123"


def test_redirect_short_url_returns_307(monkeypatch):
    monkeypatch.setattr(
        "app.main.increment_short_url_clicks",
        lambda code: ShortUrlStats(
            code=code,
            original_url="https://example.com/",
            clicks=1,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            last_accessed_at=datetime(2026, 1, 1, 0, 0, 2, tzinfo=timezone.utc),
        ),
    )

    response = client.get("/s/abc123", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/"


def test_short_url_stats_returns_record(monkeypatch):
    monkeypatch.setattr(
        "app.main.get_short_url",
        lambda code: ShortUrlStats(
            code=code,
            original_url="https://example.com/",
            clicks=4,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ),
    )

    response = client.get("/shorten/abc123/stats")

    assert response.status_code == 200
    assert response.json()["clicks"] == 4


def test_health_returns_ok(monkeypatch):
    monkeypatch.setattr("app.main.get_redis_status", lambda: "connected")

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "redis": "connected"}
