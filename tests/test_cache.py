
from app.cache import (
    clear_cache,
    delete_cached_result,
    get_all_cached_urls,
    get_cache_size,
    get_cached_result,
    has_cached_result,
    set_cached_result,
)

def test_get_cached_result_returns_none_for_missing_url():
    clear_cache()
    result = get_cached_result("https://example.com")

    assert result is None

def test_set_cached_result_stores_data():
    clear_cache()
    url = "https://example.com"
    data = {
        "short_code": "abc123",
        "data": {
            "status_code": 200,
            "content_length": 100,
            "title": "Example Domain",
            "meta_description": "Example description",
            "links": ["https://iana.org/domains/example"],
            "images": [],
            "headings": ["Example Domain"],
        },
    }

    set_cached_result(url, data)

    assert get_cached_result(url) == data

def test_has_cached_result_returns_true_for_cached_url():
    clear_cache()
    url = "https://example.com"
    data = {
        "short_code": "abc123",
        "data": {
            "status_code": 200,
            "content_length": 100,
            "title": "Example Domain",
            "meta_description": "Example description",
            "links": ["https://iana.org/domains/example"],
            "images": [],
            "headings": ["Example Domain"],
        },
    }

    set_cached_result(url, data)
    
    result = has_cached_result(url)
    assert result is True
    
def test_delete_cached_result_removes_url():
    clear_cache()
    url = "https://example.com"
    data = {
        "short_code": "abc123",
        "data": {
            "status_code": 200,
            "content_length": 100,
            "title": "Example Domain",
            "meta_description": "Example description",
            "links": ["https://iana.org/domains/example"],
            "images": [],
            "headings": ["Example Domain"],
        },
    }

    set_cached_result(url, data)
    
    delete_cached_result(url)

    assert get_cached_result(url) is None
    
    
def test_clear_cache_removes_all_entries():
    clear_cache()
    url = "https://example.com"
    data = {
        "short_code": "abc123",
        "data": {
            "status_code": 200,
            "content_length": 100,
            "title": "Example Domain",
            "meta_description": "Example description",
            "links": ["https://iana.org/domains/example"],
            "images": [],
            "headings": ["Example Domain"],
        },
    }

    set_cached_result(url, data)
    
    clear_cache()

    assert get_cache_size() == 0
    
def test_get_cache_size_returns_number_of_entries():
    clear_cache()
    url = "https://example.com"
    data = {
        "short_code": "abc123",
        "data": {
            "status_code": 200,
            "content_length": 100,
            "title": "Example Domain",
            "meta_description": "Example description",
            "links": ["https://iana.org/domains/example"],
            "images": [],
            "headings": ["Example Domain"],
        },
    }

    set_cached_result(url, data)
    
    result = get_cache_size()

    assert result == 1
    
def test_get_all_cached_urls_returns_cached_keys():
    clear_cache()
    url = "https://example.com"
    data = {
        "short_code": "abc123",
        "data": {
            "status_code": 200,
            "content_length": 100,
            "title": "Example Domain",
            "meta_description": "Example description",
            "links": ["https://iana.org/domains/example"],
            "images": [],
            "headings": ["Example Domain"],
        },
    }

    set_cached_result(url, data)
    
    result = get_all_cached_urls()

    assert result == [url]
