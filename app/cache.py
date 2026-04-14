from __future__ import annotations
from app.models import ScrapeResult

from redis import Redis


r = Redis(host="localhost", port=6379, db=0, decode_responses=True)
CACHE_TTL = 3600


def get_cached_result(url:str) -> ScrapeResult | None:
    cached_data = r.get(url)
    if cached_data is None:
        return None
    return ScrapeResult.model_validate_json(cached_data)
 
def set_cached_result(url:str, data:ScrapeResult) -> None:
    r.set(url, data.model_dump_json(), ex=CACHE_TTL)

def has_cached_result(url:str) -> bool:
    return r.exists(url) == 1 

def clear_cache() -> None:
    r.flushdb()

def delete_cached_result(url:str) -> None:
    r.delete(url)

def get_cache_size() -> int:
    return r.dbsize()

def get_all_cached_urls() -> list[str]:
    return [key for key in r.keys("*")]