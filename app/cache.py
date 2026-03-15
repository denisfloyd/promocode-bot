from cachetools import TTLCache

from app.config import settings

cache = TTLCache(maxsize=256, ttl=settings.cache_ttl)


def clear_cache():
    cache.clear()
