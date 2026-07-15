"""Redis-backed failed ID store.

Persists failed IDs uncapped in Redis sets for O(1) lookup.
Provides a simple API for checking and adding failed IDs across categories.
"""

from typing import Iterable

from app.redis import RedisClient, Namespace


class FailedIdStore:
    """Store failed IDs in Redis sets, one set per category.

    Categories map to Redis set keys:
        "beatmaps"       -> "failed_ids:beatmaps"
        "beatmapsets"    -> "failed_ids:beatmapsets"
        "users"          -> "failed_ids:users:{ruleset}" (e.g. "failed_ids:users:osu")
        "users.{ruleset}" -> "failed_ids:users:{ruleset}"
    """

    def __init__(self, rc: RedisClient):
        self.rc = rc

    def _key(self, category: str, subcategory: str | None = None) -> str:
        if category == "users" and subcategory:
            return f"{Namespace.FAILED_IDS}:{subcategory}"
        return f"{Namespace.FAILED_IDS}:{category}"

    async def is_failed(self, category: str, id_: int, subcategory: str | None = None) -> bool:
        """Check if an ID has failed in the given category. O(1)."""
        key = self._key(category, subcategory)
        return await self.rc.sismember(key, id_)

    async def add_failed(self, category: str, id_: int, subcategory: str | None = None) -> None:
        """Add an ID to the failed set for the given category."""
        key = self._key(category, subcategory)
        await self.rc.sadd(key, id_)

    async def add_many(
        self, category: str, ids: Iterable[int], subcategory: str | None = None
    ) -> None:
        """Add multiple IDs to the failed set."""
        key = self._key(category, subcategory)
        if ids:
            await self.rc.sadd(key, *ids)

    async def load_all(self) -> dict[str, set[int]]:
        """Load all failed IDs from Redis into a dict for use by RandomIDSource."""
        result: dict[str, set[int]] = {}
        pattern = f"{Namespace.FAILED_IDS}:*"
        async for key in self.rc.scan_iter(match=pattern):
            set_name = key.removeprefix(f"{Namespace.FAILED_IDS}:")
            members = await self.rc.smembers(key)
            result[set_name] = {int(m) for m in members}
        return result

    async def clear_category(self, category: str, subcategory: str | None = None) -> int:
        """Delete all failed IDs for a category. Returns number of keys deleted."""
        key = self._key(category, subcategory)
        return await self.rc.delete(key)

    async def clear_all(self) -> int:
        """Delete all failed ID sets. Returns number of keys deleted."""
        pattern = f"{Namespace.FAILED_IDS}:*"
        keys = []
        async for key in self.rc.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            return await self.rc.delete(*keys)
        return 0
