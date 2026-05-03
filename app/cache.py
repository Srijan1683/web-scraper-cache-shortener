from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from app.models import ScrapeJobResponse, ScrapeResult, ShortUrlStats
from app.summary_models import SummarizationResult
from pydantic import ValidationError

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


def _delete_key(key: str) -> None:
    redis_client = _get_redis_client()
    if redis_client is not None:
        redis_client.delete(key)
        return

    _memory_cache.pop(key, None)


def get_redis_status() -> str:
    redis_client = _get_redis_client()
    if redis_client is None:
        return "disconnected"

    try:
        redis_client.ping()
    except Exception:
        return "disconnected"

    return "connected"


def get_cached_result(url: str) -> Optional[ScrapeResult]:
    cache_key = url
    redis_client = _get_redis_client()
    if redis_client is not None:
        cached_data = redis_client.get(cache_key)
        if cached_data is None:
            return None
        try:
            return ScrapeResult.model_validate_json(cached_data)
        except ValidationError:
            redis_client.delete(cache_key)
            return None

    _purge_expired_memory_entries()
    cached_entry = _memory_cache.get(cache_key)
    if cached_entry is None:
        return None

    _, cached_data = cached_entry
    try:
        return ScrapeResult.model_validate_json(cached_data)
    except ValidationError:
        _memory_cache.pop(cache_key, None)
        return None


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


def delete_cached_markdown(url: str) -> None:
    redis_client = _get_redis_client()
    markdown_key = f"markdown:{url}"

    if redis_client is not None:
        redis_client.delete(markdown_key)
        return

    _memory_cache.pop(markdown_key, None)


def get_cached_summary(url: str, summary_type: str) -> Optional[SummarizationResult]:
    redis_client = _get_redis_client()
    summary_key = f"summary:{summary_type}:{url}"

    if redis_client is not None:
        cached_data = redis_client.get(summary_key)
        if cached_data is None:
            return None
        try:
            return SummarizationResult.model_validate_json(cached_data)
        except ValidationError:
            redis_client.delete(summary_key)
            return None

    _purge_expired_memory_entries()
    cached_entry = _memory_cache.get(summary_key)
    if cached_entry is None:
        return None

    _, cached_data = cached_entry
    try:
        return SummarizationResult.model_validate_json(cached_data)
    except ValidationError:
        _memory_cache.pop(summary_key, None)
        return None


def set_cached_summary(url: str, summary_type: str, data: SummarizationResult) -> None:
    serialized_data = data.model_dump_json()
    redis_client = _get_redis_client()
    summary_key = f"summary:{summary_type}:{url}"

    if redis_client is not None:
        redis_client.set(summary_key, serialized_data, ex=CACHE_TTL)
        return

    _memory_cache[summary_key] = (time.time() + CACHE_TTL, serialized_data)


def delete_cached_summary(url: str, summary_type: str) -> None:
    redis_client = _get_redis_client()
    summary_key = f"summary:{summary_type}:{url}"

    if redis_client is not None:
        redis_client.delete(summary_key)
        return

    _memory_cache.pop(summary_key, None)


def get_cached_job(job_id: str) -> Optional[ScrapeJobResponse]:
    redis_client = _get_redis_client()
    job_key = f"job:{job_id}"

    if redis_client is not None:
        cached_data = redis_client.get(job_key)
        if cached_data is None:
            return None
        try:
            return ScrapeJobResponse.model_validate_json(cached_data)
        except ValidationError:
            redis_client.delete(job_key)
            return None

    _purge_expired_memory_entries()
    cached_entry = _memory_cache.get(job_key)
    if cached_entry is None:
        return None

    _, cached_data = cached_entry
    try:
        return ScrapeJobResponse.model_validate_json(cached_data)
    except ValidationError:
        _memory_cache.pop(job_key, None)
        return None


def set_cached_job(job_id: str, data: ScrapeJobResponse) -> None:
    serialized_data = data.model_dump_json()
    redis_client = _get_redis_client()
    job_key = f"job:{job_id}"

    if redis_client is not None:
        redis_client.set(job_key, serialized_data, ex=CACHE_TTL)
        return

    _memory_cache[job_key] = (time.time() + CACHE_TTL, serialized_data)


def delete_cached_job(job_id: str) -> None:
    redis_client = _get_redis_client()
    job_key = f"job:{job_id}"

    if redis_client is not None:
        redis_client.delete(job_key)
        return

    _memory_cache.pop(job_key, None)


def get_job_id_for_url(url: str, summary_type: str) -> Optional[str]:
    redis_client = _get_redis_client()
    job_lookup_key = f"job-map:{summary_type}:{url}"

    if redis_client is not None:
        return redis_client.get(job_lookup_key)

    _purge_expired_memory_entries()
    cached_entry = _memory_cache.get(job_lookup_key)
    if cached_entry is None:
        return None

    _, job_id = cached_entry
    return job_id


def set_job_id_for_url(url: str, summary_type: str, job_id: str) -> None:
    redis_client = _get_redis_client()
    job_lookup_key = f"job-map:{summary_type}:{url}"

    if redis_client is not None:
        redis_client.set(job_lookup_key, job_id, ex=CACHE_TTL)
        return

    _memory_cache[job_lookup_key] = (time.time() + CACHE_TTL, job_id)


def delete_job_id_for_url(url: str, summary_type: str) -> None:
    redis_client = _get_redis_client()
    job_lookup_key = f"job-map:{summary_type}:{url}"

    if redis_client is not None:
        redis_client.delete(job_lookup_key)
        return

    _memory_cache.pop(job_lookup_key, None)


def get_short_url(code: str) -> Optional[ShortUrlStats]:
    redis_client = _get_redis_client()
    short_key = f"short:{code}"

    if redis_client is not None:
        cached_data = redis_client.get(short_key)
        if cached_data is None:
            return None
        try:
            return ShortUrlStats.model_validate_json(cached_data)
        except ValidationError:
            redis_client.delete(short_key)
            return None

    _purge_expired_memory_entries()
    cached_entry = _memory_cache.get(short_key)
    if cached_entry is None:
        return None

    _, cached_data = cached_entry
    try:
        return ShortUrlStats.model_validate_json(cached_data)
    except ValidationError:
        _memory_cache.pop(short_key, None)
        return None


def set_short_url(code: str, data: ShortUrlStats) -> None:
    serialized_data = data.model_dump_json()
    redis_client = _get_redis_client()
    short_key = f"short:{code}"

    if redis_client is not None:
        redis_client.set(short_key, serialized_data, ex=CACHE_TTL)
        return

    _memory_cache[short_key] = (time.time() + CACHE_TTL, serialized_data)


def increment_short_url_clicks(code: str) -> Optional[ShortUrlStats]:
    cached_short_url = get_short_url(code)
    if cached_short_url is None:
        return None

    updated_short_url = cached_short_url.model_copy(
        update={
            "clicks": cached_short_url.clicks + 1,
            "last_accessed_at": datetime.now(timezone.utc),
        }
    )
    set_short_url(code, updated_short_url)
    return updated_short_url


def delete_short_url(code: str) -> None:
    redis_client = _get_redis_client()
    short_key = f"short:{code}"

    if redis_client is not None:
        redis_client.delete(short_key)
        return

    _memory_cache.pop(short_key, None)
