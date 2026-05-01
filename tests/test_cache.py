from datetime import datetime, timezone

from app.cache import (
    clear_cache,
    delete_cached_result,
    get_all_cached_urls,
    get_cache_size,
    get_cached_markdown,
    get_cached_result,
    get_cached_summary,
    has_cached_result,
    increment_result_clicks,
    set_cached_markdown,
    set_cached_result,
    set_cached_summary,
)
from app.models import ScrapeResponse, ScrapeResult
from app.summary_models import SummarizationResult, TokenUsage


def build_scrape_result(url: str = "https://example.com") -> ScrapeResult:
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
        token_usage=TokenUsage(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
        ),
    )

def test_get_cached_result_returns_none_for_missing_url():
    clear_cache()
    result = get_cached_result("https://example.com")

    assert result is None

def test_set_cached_result_stores_data():
    clear_cache()
    url = "https://example.com"
    data = build_scrape_result(url)

    set_cached_result(url, data)

    assert get_cached_result(url) == data

def test_has_cached_result_returns_true_for_cached_url():
    clear_cache()
    url = "https://example.com"
    data = build_scrape_result(url)

    set_cached_result(url, data)
    
    result = has_cached_result(url)
    assert result is True
    
def test_delete_cached_result_removes_url():
    clear_cache()
    url = "https://example.com"
    data = build_scrape_result(url)

    set_cached_result(url, data)
    
    delete_cached_result(url)

    assert get_cached_result(url) is None
    
    
def test_clear_cache_removes_all_entries():
    clear_cache()
    url = "https://example.com"
    data = build_scrape_result(url)

    set_cached_result(url, data)
    
    clear_cache()

    assert get_cache_size() == 0
    
def test_get_cache_size_returns_number_of_entries():
    clear_cache()
    url = "https://example.com"
    data = build_scrape_result(url)

    set_cached_result(url, data)
    
    result = get_cache_size()

    assert result == 1
    
def test_get_all_cached_urls_returns_cached_keys():
    clear_cache()
    url = "https://example.com"
    data = build_scrape_result(url)

    set_cached_result(url, data)
    
    result = get_all_cached_urls()

    assert result == [url]


def test_increment_result_clicks_updates_cached_result():
    clear_cache()
    url = "https://example.com"
    set_cached_result(url, build_scrape_result(url))

    updated_result = increment_result_clicks(url)

    assert updated_result is not None
    assert updated_result.clicks == 1
    assert get_cached_result(url).clicks == 1


def test_set_cached_markdown_stores_markdown_content():
    clear_cache()
    url = "https://example.com"
    markdown_content = "# Example Domain\n\nHello world."

    set_cached_markdown(url, markdown_content)

    assert get_cached_markdown(url) == markdown_content


def test_get_cache_size_counts_structured_and_markdown_entries():
    clear_cache()
    url = "https://example.com"

    set_cached_result(url, build_scrape_result(url))
    set_cached_markdown(url, "# Example Domain")

    assert get_cache_size() == 2


def test_set_cached_summary_stores_summary_result():
    clear_cache()
    url = "https://example.com"
    summary_type = "brief"
    summary_result = build_summary_result()

    set_cached_summary(url, summary_type, summary_result)

    assert get_cached_summary(url, summary_type) == summary_result
