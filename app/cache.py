from __future__ import annotations
from typing import Any

url_cache: dict[str,Any] = {}

def get_cached_result(url) -> Any:
    return url_cache.get(url)
 
def set_cached_result(url,data):
    url_cache[url] = data

def has_cached_result(url) -> bool:
    return url in url_cache

def clear_cache() -> None:
    url_cache.clear()

def delete_cached_result(url) -> None:
    url_cache.pop(url, None)

def get_cache_size() -> int:
    return len(url_cache)
    
def get_all_cached_urls() -> list[str]:
    return list(url_cache.keys())
