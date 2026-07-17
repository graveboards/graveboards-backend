import hashlib
import json
from enum import Enum

from app.redis import RedisClient
from app.search.enums import Scope


class CacheTTLConfig(Enum):
    """Configurable TTL per search scope."""
    BEATMAP = 120
    BEATMAPSET = 300
    PROFILE = 60
    REQUEST = 180
    QUEUE = 300
    SCORE = 60
    USER = 120


class SearchCache:
    """Redis-backed cache for search results.

    Cache key: hash of (scope, search_terms, sorting, filters, limit, offset)
    Cache value: serialized Page object
    TTL: configurable per scope
    """
    CACHE_PREFIX = "search_cache"
    MAX_VALUE_SIZE = 1024 * 1024

    def __init__(self, rc: RedisClient):
        self.rc = rc

    def _make_key(self, scope: Scope, search_terms: str, sorting: str,
                  filters: str, limit: int, offset: int) -> str:
        raw = f"{scope.value}:{search_terms}:{sorting}:{filters}:{limit}:{offset}"
        hash_key = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return f"{self.CACHE_PREFIX}:{scope.value}:{hash_key}"

    def _get_ttl(self, scope: Scope) -> int:
        return CacheTTLConfig[scope.name.upper()].value

    async def get(self, scope: Scope, search_terms: str, sorting: str,
                  filters: str, limit: int, offset: int) -> dict | None:
        key = self._make_key(scope, search_terms, sorting, filters, limit, offset)
        data = await self.rc.get(key)
        if data:
            return json.loads(data)
        return None

    async def set(self, scope: Scope, search_terms: str, sorting: str,
                  filters: str, limit: int, offset: int, page_data: dict):
        serialized = json.dumps(page_data)
        if len(serialized) > self.MAX_VALUE_SIZE:
            return

        key = self._make_key(scope, search_terms, sorting, filters, limit, offset)
        ttl = self._get_ttl(scope)
        await self.rc.set(key, serialized, ex=ttl)

    async def invalidate_scope(self, scope: Scope):
        """Invalidate all cached results for a scope (on data changes)."""
        pattern = f"{self.CACHE_PREFIX}:{scope.value}:*"
        async for key in self.rc.scan(pattern):
            await self.rc.delete(key)
