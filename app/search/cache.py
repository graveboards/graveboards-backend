"""Redis-backed search result caching."""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import TYPE_CHECKING, Any
from typing import cast as typing_cast

if TYPE_CHECKING:
    from app.redis_client import RedisClient
    from app.search.enums import Scope


class CacheTTLConfig(Enum):
    """Configurable TTL per search scope."""

    BEATMAP = 120
    BEATMAPSET = 300
    PROFILE = 60
    REQUEST = 180


class SearchCache:
    """Redis-backed cache for search results.

    Cache key: hash of (scope, search_terms, sorting, filters, limit, offset)
    Cache value: serialized Page object
    TTL: configurable per scope
    """

    CACHE_PREFIX = "search_cache"
    MAX_VALUE_SIZE = 1024 * 1024

    def __init__(self, rc: RedisClient):
        """Initialize the search cache.

        Args:
            rc:
                Redis client for cache operations.
        """
        self.rc = rc

    def _make_key(
        self, scope: Scope, search_terms: str, sorting: str, filters: str, limit: int, offset: int
    ) -> str:
        """Generate a cache key from search parameters.

        Args:
            scope:
                The search scope.
            search_terms:
                The search query string.
            sorting:
                Serialized sorting parameters.
            filters:
                Serialized filter parameters.
            limit:
                Result limit.
            offset:
                Result offset.

        Returns:
            A deterministic cache key string.
        """
        raw = f"{scope.value}:{search_terms}:{sorting}:{filters}:{limit}:{offset}"
        hash_key = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return f"{self.CACHE_PREFIX}:{scope.value}:{hash_key}"

    def _get_ttl(self, scope: Scope) -> int:
        """Get the cache TTL for a given scope.

        Args:
            scope:
                The search scope.

        Returns:
            TTL in seconds.
        """
        return CacheTTLConfig[scope.name.upper()].value

    async def get(
        self, scope: Scope, search_terms: str, sorting: str, filters: str, limit: int, offset: int
    ) -> dict | None:
        """Retrieve cached search results.

        Args:
            scope:
                The search scope.
            search_terms:
                The search query string.
            sorting:
                Serialized sorting parameters.
            filters:
                Serialized filter parameters.
            limit:
                Result limit.
            offset:
                Result offset.

        Returns:
            Cached page data, or None if not cached.
        """
        key = self._make_key(scope, search_terms, sorting, filters, limit, offset)
        data = await self.rc.get(key)
        if data:
            return typing_cast("dict[Any, Any]", json.loads(data))
        return None

    async def set(
        self,
        scope: Scope,
        search_terms: str,
        sorting: str,
        filters: str,
        limit: int,
        offset: int,
        page_data: dict[str, Any],
    ) -> None:
        """Cache search results with a scope-specific TTL.

        Args:
            scope:
                The search scope.
            search_terms:
                The search query string.
            sorting:
                Serialized sorting parameters.
            filters:
                Serialized filter parameters.
            limit:
                Result limit.
            offset:
                Result offset.
            page_data:
                The page data to cache.
        """
        serialized = json.dumps(page_data)
        if len(serialized) > self.MAX_VALUE_SIZE:
            return

        key = self._make_key(scope, search_terms, sorting, filters, limit, offset)
        ttl = self._get_ttl(scope)
        await self.rc.set(key, serialized, ex=ttl)

    async def invalidate_scope(self, scope: Scope) -> None:
        """Invalidate all cached results for a scope (on data changes)."""
        pattern = f"{self.CACHE_PREFIX}:{scope.value}:*"
        async for key in self.rc.scan_iter(match=pattern):
            await self.rc.delete(key)
