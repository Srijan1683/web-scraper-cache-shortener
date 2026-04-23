from __future__ import annotations

import os
import time
from typing import Optional, TYPE_CHECKING

from app.models import ScrapeResult

if TYPE_CHECKING:
    from redis import Redis as RedisClient
else:
    RedisClient = object

try:
    from redis import Redis
except ModuleNotFoundError:
    Redis = None


CACHE_TTL = 3600
REDIS_URL = os.getenv("REDIS_URL", "").strip()

_memory_cache: dict[str, tuple[float, str]] = {}


def _purge_expired_memory_entries() -> None:
    now = time.time()
    expired_urls = [url for url, (expires_at, _) in _memory_cache.items() if expires_at <= now]
    for url in expired_urls:
        _memory_cache.pop(url, None)


def _get_redis_client() -> Optional[RedisClient]:
    if Redis is None or not REDIS_URL:
        return None

    return Redis.from_url(REDIS_URL, decode_responses=True)


def get_cached_result(url: str) -> Optional[ScrapeResult]:
    redis_client = _get_redis_client()
    if redis_client is not None:
        cached_data = redis_client.get(url)
        if cached_data is None:
            return None
        return ScrapeResult.model_validate_json(cached_data)

    _purge_expired_memory_entries()
    cached_entry = _memory_cache.get(url)
    if cached_entry is None:
        return None

    _, cached_data = cached_entry
    return ScrapeResult.model_validate_json(cached_data)


def set_cached_result(url: str, data: ScrapeResult) -> None:
    serialized_data = data.model_dump_json()
    redis_client = _get_redis_client()
    if redis_client is not None:
        redis_client.set(url, serialized_data, ex=CACHE_TTL)
        return

    _memory_cache[url] = (time.time() + CACHE_TTL, serialized_data)


def increment_result_clicks(url: str) -> Optional[ScrapeResult]:
    cached_result = get_cached_result(url)
    if cached_result is None:
        return None

    updated_result = cached_result.model_copy(update={"clicks": cached_result.clicks + 1})
    set_cached_result(url, updated_result)
    return updated_result


def has_cached_result(url: str) -> bool:
    return get_cached_result(url) is not None


def clear_cache() -> None:
    redis_client = _get_redis_client()
    if redis_client is not None:
        redis_client.flushdb()
        return

    _memory_cache.clear()


def delete_cached_result(url: str) -> None:
    redis_client = _get_redis_client()
    if redis_client is not None:
        redis_client.delete(url)
        return

    _memory_cache.pop(url, None)


def get_cache_size() -> int:
    redis_client = _get_redis_client()
    if redis_client is not None:
        return int(redis_client.dbsize())

    _purge_expired_memory_entries()
    return len(_memory_cache)


def get_all_cached_urls() -> list[str]:
    redis_client = _get_redis_client()
    if redis_client is not None:
        return [key for key in redis_client.keys("*")]

    _purge_expired_memory_entries()
    return list(_memory_cache.keys())

def get_cached_markdown(url: str) -> Optional[str]:
    redis_client = _get_redis_client()
    markdown_key = f"markdown:{url}"

    if redis_client is not None:
        return redis_client.get(markdown_key)

    _purge_expired_memory_entries()
    cached_entry = _memory_cache.get(markdown_key)
    if cached_entry is None:
        return None

    _, markdown_content = cached_entry
    return markdown_content

def set_cached_markdown(url: str, markdown_content: str) -> None:
    redis_client = _get_redis_client()
    markdown_key = f"markdown:{url}"

    if redis_client is not None:
        redis_client.set(markdown_key, markdown_content, ex=CACHE_TTL)
        return

    _memory_cache[markdown_key] = (time.time() + CACHE_TTL, markdown_content)
