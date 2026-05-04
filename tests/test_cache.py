from datetime import datetime, timezone
import time

import app.cache as cache_module
from app.cache import (
    clear_cache,
    delete_cached_job,
    delete_cached_markdown,
    delete_cached_result,
    delete_cached_summary,
    delete_job_id_for_url,
    delete_short_url,
    get_cache_size,
    get_cached_job,
    get_cached_markdown,
    get_cached_result,
    get_cached_summary,
    get_job_id_for_url,
    get_short_url,
    increment_result_clicks,
    increment_short_url_clicks,
    set_cached_job,
    set_cached_markdown,
    set_cached_result,
    set_cached_summary,
    set_job_id_for_url,
    set_short_url,
)
from app.models import ScrapeJobResponse, ScrapeResponse, ScrapeResult, ShortUrlStats
from app.summary_models import SummarizationResult, TokenUsage


def build_scrape_result(url: str = "https://example.com/") -> ScrapeResult:
    return ScrapeResult(
        short_code="abc123",
        original_url=url,
        clicks=0,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        data=ScrapeResponse(
            url=url,
            status_code=200,
            status="crawling",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            completed_at=datetime(2026, 1, 1, 0, 0, 5, tzinfo=timezone.utc),
            content_length=100,
            title="Example Domain",
            meta_description="Example description",
            links=["https://iana.org/domains/example"],
            images=[],
            headings=["Example Domain"],
        ),
    )


def build_summary_result() -> SummarizationResult:
    return SummarizationResult(
        summary="Example summary",
        model="openai/gpt-4o-mini",
        token_usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )


def build_job() -> ScrapeJobResponse:
    result = build_scrape_result()
    return ScrapeJobResponse(
        job_id="job-123",
        original_url="https://example.com/",
        summary_type="brief",
        status="completed",
        created_at=result.created_at,
        completed_at=result.data.completed_at,
        short_code=result.short_code,
        result=result,
        summary=build_summary_result(),
    )


def build_short_url_stats(code: str = "abc123") -> ShortUrlStats:
    return ShortUrlStats(
        code=code,
        original_url="https://example.com/",
        clicks=0,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def test_set_cached_result_stores_data():
    clear_cache()
    url = "https://example.com/"
    data = build_scrape_result(url)

    set_cached_result(url, data)

    assert get_cached_result(url) == data


def test_increment_result_clicks_updates_cached_result():
    clear_cache()
    url = "https://example.com/"
    set_cached_result(url, build_scrape_result(url))

    updated_result = increment_result_clicks(url)

    assert updated_result is not None
    assert updated_result.clicks == 1
    assert get_cached_result(url).clicks == 1


def test_delete_cached_result_removes_url():
    clear_cache()
    url = "https://example.com/"
    set_cached_result(url, build_scrape_result(url))

    delete_cached_result(url)

    assert get_cached_result(url) is None


def test_set_cached_markdown_stores_markdown_content():
    clear_cache()
    url = "https://example.com/"

    set_cached_markdown(url, "# Example Domain")

    assert get_cached_markdown(url) == "# Example Domain"


def test_delete_cached_markdown_removes_markdown():
    clear_cache()
    url = "https://example.com/"
    set_cached_markdown(url, "# Example Domain")

    delete_cached_markdown(url)

    assert get_cached_markdown(url) is None


def test_set_cached_summary_stores_summary_result():
    clear_cache()
    url = "https://example.com/"
    summary_result = build_summary_result()

    set_cached_summary(url, "brief", summary_result)

    assert get_cached_summary(url, "brief") == summary_result


def test_delete_cached_summary_removes_summary():
    clear_cache()
    url = "https://example.com/"
    set_cached_summary(url, "brief", build_summary_result())

    delete_cached_summary(url, "brief")

    assert get_cached_summary(url, "brief") is None


def test_set_cached_job_stores_job():
    clear_cache()
    job = build_job()

    set_cached_job(job.job_id, job)

    assert get_cached_job(job.job_id) == job


def test_delete_cached_job_removes_job():
    clear_cache()
    job = build_job()
    set_cached_job(job.job_id, job)

    delete_cached_job(job.job_id)

    assert get_cached_job(job.job_id) is None


def test_set_job_id_for_url_stores_lookup():
    clear_cache()
    set_job_id_for_url("https://example.com/", "brief", "job-123")

    assert get_job_id_for_url("https://example.com/", "brief") == "job-123"


def test_delete_job_id_for_url_removes_lookup():
    clear_cache()
    set_job_id_for_url("https://example.com/", "brief", "job-123")

    delete_job_id_for_url("https://example.com/", "brief")

    assert get_job_id_for_url("https://example.com/", "brief") is None


def test_set_short_url_and_increment_clicks():
    clear_cache()
    short_url_stats = build_short_url_stats()
    set_short_url(short_url_stats.code, short_url_stats)

    updated_short_url = increment_short_url_clicks(short_url_stats.code)

    assert updated_short_url is not None
    assert updated_short_url.clicks == 1
    assert updated_short_url.last_accessed_at is not None
    assert get_short_url(short_url_stats.code).clicks == 1


def test_delete_short_url_removes_record():
    clear_cache()
    short_url_stats = build_short_url_stats()
    set_short_url(short_url_stats.code, short_url_stats)

    delete_short_url(short_url_stats.code)

    assert get_short_url(short_url_stats.code) is None


def test_get_cache_size_counts_multiple_entry_types():
    clear_cache()
    set_cached_result("https://example.com/", build_scrape_result())
    set_cached_markdown("https://example.com/", "# Example Domain")
    set_cached_summary("https://example.com/", "brief", build_summary_result())
    set_cached_job("job-123", build_job())

    assert get_cache_size() == 4


def test_get_cached_result_discards_invalid_cached_schema():
    clear_cache()
    cache_module._memory_cache["https://example.com/"] = (time.time() + 3600, '{"invalid": true}')

    result = get_cached_result("https://example.com/")

    assert result is None
    assert "https://example.com/" not in cache_module._memory_cache


def test_get_cached_job_discards_invalid_cached_schema():
    clear_cache()
    cache_module._memory_cache["job:job-123"] = (time.time() + 3600, '{"invalid": true}')

    result = get_cached_job("job-123")

    assert result is None
    assert "job:job-123" not in cache_module._memory_cache
