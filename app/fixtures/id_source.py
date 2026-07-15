"""Pluggable ID source strategies for fixture fetching.

Each ID source provides a way to resolve which IDs to fetch from the osu! API.
Sources are tried in priority order: archive (most reliable) -> top players
(moderately reliable) -> random guessing (least reliable).

Usage:
    source = AutoIDSource(rc)
    await source.resolve()
    id_ = source.get_id("beatmaps")
"""

import asyncio
import random
from abc import ABC, abstractmethod
from typing import Optional

from app.redis import RedisClient
from app.fixtures.metadata_io import load_metadata, load_top_player_ids
from app.fixtures.constants import ID_RANGES, TOP_PLAYERS_PER_RULESET
from app.fixtures.archives import (
    refresh_archive_index,
    load_archive_index,
    get_user_ids_from_archive,
    get_beatmap_ids_from_archive,
)
from app.fixtures.failed_id_store import FailedIdStore
from app.logging import get_logger

logger = get_logger(__name__)


class IDSource(ABC):
    """Base class for ID resolution strategies."""

    name: str = "base"

    @abstractmethod
    async def resolve(self) -> bool:
        """Pre-load IDs. Return True if source has usable data."""

    @abstractmethod
    async def get_id(self, category: str, subcategory: str | None = None) -> int | None:
        """Get a single ID for the given category. Returns None if exhausted."""

    def has_ids(self, category: str, subcategory: str | None = None) -> bool:
        """Check if source has any IDs for the given category."""
        return False


class RandomIDSource(IDSource):
    """Random ID guessing with failed-ID avoidance.

    This is the fallback strategy. It generates random IDs within configured
    ranges and tracks failed IDs to avoid retrying them.
    Uses FailedIdStore for uncapped, persistent failed ID tracking.
    """

    name = "random"

    def __init__(self, id_ranges: dict | None = None, failed_id_store: FailedIdStore | None = None):
        self.id_ranges = id_ranges or ID_RANGES
        self.failed_id_store = failed_id_store
        self._failed_cache: dict[str, set[int]] = {}
        self._pool: dict[str, list[int]] = {}

    async def resolve(self) -> bool:
        if self.failed_id_store:
            self._failed_cache = await self.failed_id_store.load_all()
        return True

    async def get_id(self, category: str, subcategory: str | None = None) -> int | None:
        key = f"{category}.{subcategory}" if subcategory else category
        failed = self._failed_cache.get(key, set())

        range_config = self.id_ranges.get(
            category, self.id_ranges.get(key.split(".")[0], {"min": 1, "max": 1000000})
        )
        min_id = range_config.get("min", 1)
        max_id = range_config.get("max", 1000000)

        for _ in range(100):
            candidate = random.randint(min_id, max_id)
            if candidate not in failed:
                return candidate
        return random.randint(min_id, max_id)

    async def add_failed(self, category: str, id_: int, subcategory: str | None = None) -> None:
        if self.failed_id_store:
            await self.failed_id_store.add_failed(category, id_, subcategory)

        key = f"{category}.{subcategory}" if subcategory else category
        if key not in self._failed_cache:
            self._failed_cache[key] = set()
        self._failed_cache[key].add(id_)

    def has_ids(self, category: str, subcategory: str | None = None) -> bool:
        return True


class TopPlayerIDSource(IDSource):
    """Use top player IDs from metadata.json.

    These come from the osu! API rankings endpoint and are moderately reliable.
    """

    name = "top_players"

    def __init__(self):
        self.player_ids: dict[str, list[int]] = {}
        self._indices: dict[str, int] = {}
        self._loaded = False

    async def resolve(self) -> bool:
        metadata = load_metadata()
        self.player_ids = metadata.get("top_player_ids", {})
        total = sum(len(ids) for ids in self.player_ids.values())
        self._indices = {r: 0 for r in self.player_ids}
        self._loaded = total > 0
        if self._loaded:
            logger.info(
                f"TopPlayerIDSource: loaded {total} player IDs across {len(self.player_ids)} rulesets"
            )
        return self._loaded

    async def get_id(self, category: str, subcategory: str | None = None) -> int | None:
        if not self._loaded:
            return None

        if subcategory and subcategory in self.player_ids:
            ids = self.player_ids[subcategory]
            idx = self._indices.get(subcategory, 0)
            if idx < len(ids):
                self._indices[subcategory] = idx + 1
                return ids[idx]
            return None

        for ruleset, ids in self.player_ids.items():
            idx = self._indices.get(ruleset, 0)
            if idx < len(ids):
                self._indices[ruleset] = idx + 1
                return ids[idx]
        return None

    def has_ids(self, category: str, subcategory: str | None = None) -> bool:
        if not self._loaded:
            return False
        if subcategory:
            return bool(self.player_ids.get(subcategory))
        return any(len(ids) > 0 for ids in self.player_ids.values())


class ArchiveIDSource(IDSource):
    """Use osu.sh SQL archive dumps as the primary ID source.

    This is the most reliable source: it extracts real player and beatmap IDs
    from structured SQL dumps downloaded from data.ppy.sh.

    Implements lazy loading: resolve() only loads the index metadata (instant).
    IDs are parsed on-demand when get_id() is called for the first time.
    """

    name = "archive"

    def __init__(self, allow_download: bool = False, pre_load: bool = False):
        self.player_ids: dict[str, list[int]] = {}
        self.beatmap_ids: list[int] = []
        self._player_indices: dict[str, int] = {}
        self._beatmap_index = 0
        self._loaded = False
        self.allow_download = allow_download
        self.pre_load = pre_load
        self._archive_index = None
        self._player_ids_loaded: dict[str, bool] = {}
        self._beatmap_ids_loaded = False
        self._resolve_called = False

    async def resolve(self) -> bool:
        try:
            if self.allow_download:
                logger.info("Refreshing archive index from osu.sh...")
                self._archive_index = await refresh_archive_index()
            else:
                logger.debug("Loading cached archive index...")
                self._archive_index = load_archive_index()
        except Exception as e:
            logger.warning(f"ArchiveIDSource: failed to load archive index: {e}")
            return False

        self._loaded = True
        self._resolve_called = True
        return True

    async def _ensure_player_ids_loaded(self, ruleset: str) -> None:
        """Lazily load player IDs for a specific ruleset on first access."""
        if self._player_ids_loaded.get(ruleset, False):
            return

        if not self._archive_index:
            return

        logger.debug(f"ArchiveIDSource: lazily loading player IDs for {ruleset}...")
        top_archive = self._archive_index.get_latest_archive(
            archive_type="performance",
            ruleset=ruleset,
            selection="top",
        )
        if top_archive:
            ids = await get_user_ids_from_archive(
                top_archive,
                min_playcount=50,
                allow_download=self.allow_download,
            )
            if ids:
                self.player_ids[ruleset] = ids[:TOP_PLAYERS_PER_RULESET]
                self._player_ids_loaded[ruleset] = True
                logger.debug(f"ArchiveIDSource: loaded {len(ids)} player IDs for {ruleset}")

    async def _ensure_beatmap_ids_loaded(self) -> None:
        """Lazily load beatmap IDs on first access."""
        if self._beatmap_ids_loaded:
            return

        if not self._archive_index:
            return

        logger.debug("ArchiveIDSource: lazily loading beatmap IDs...")
        osu_files_archive = self._archive_index.get_latest_archive(archive_type="osu_files")
        if osu_files_archive:
            self.beatmap_ids = await get_beatmap_ids_from_archive(
                osu_files_archive,
                allow_download=self.allow_download,
            )
            self._beatmap_ids_loaded = True
            logger.debug(f"ArchiveIDSource: loaded {len(self.beatmap_ids)} beatmap IDs")

    async def get_id(self, category: str, subcategory: str | None = None) -> int | None:
        if not self._loaded:
            return None

        await self._resolve_lazy(category, subcategory)

        if category == "beatmaps":
            if self._beatmap_ids_loaded and self.beatmap_ids:
                if self._beatmap_index < len(self.beatmap_ids):
                    id_ = self.beatmap_ids[self._beatmap_index]
                    self._beatmap_index += 1
                    return id_
            return None

        if subcategory and subcategory in self.player_ids:
            ids = self.player_ids[subcategory]
            idx = self._player_indices.get(subcategory, 0)
            if idx < len(ids):
                self._player_indices[subcategory] = idx + 1
                return ids[idx]
            return None

        for ruleset, ids in self.player_ids.items():
            idx = self._player_indices.get(ruleset, 0)
            if idx < len(ids):
                self._player_indices[ruleset] = idx + 1
                return ids[idx]
        return None

    async def _resolve_lazy(self, category: str, subcategory: str | None = None) -> None:
        """Resolve lazy loading for the requested category."""
        if category == "beatmaps":
            await self._ensure_beatmap_ids_loaded()
        elif category == "beatmapsets":
            return
        else:
            ruleset = subcategory or "osu"
            await self._ensure_player_ids_loaded(ruleset)

    def has_ids(self, category: str, subcategory: str | None = None) -> bool:
        if not self._loaded:
            return False
        if category == "beatmaps":
            return self._beatmap_ids_loaded and len(self.beatmap_ids) > 0
        if subcategory:
            return bool(self.player_ids.get(subcategory))
        return any(len(ids) > 0 for ids in self.player_ids.values())


class AutoIDSource(IDSource):
    """Chain multiple ID sources: archive -> top players -> random.

    Tries each source in order. Falls back to the next when the current
    source is exhausted or unavailable.
    """

    name = "auto"

    def __init__(
        self,
        rc: RedisClient | None = None,
        id_ranges: dict | None = None,
        failed_id_store: FailedIdStore | None = None,
    ):
        self.sources: list[IDSource] = []
        self._current: IDSource | None = None
        self._resolved = False

        if rc is not None:
            self.sources.append(ArchiveIDSource(pre_load=False))
            self.sources.append(TopPlayerIDSource())
        self.sources.append(RandomIDSource(id_ranges=id_ranges, failed_id_store=failed_id_store))

    async def resolve(self) -> bool:
        for source in self.sources:
            try:
                if await source.resolve():
                    self._current = source
                    logger.info(f"AutoIDSource: using {source.name} source")
                    self._resolved = True
                    return True
            except Exception as e:
                logger.debug(f"AutoIDSource: {source.name} failed: {e}")
                continue
        self._resolved = False
        return False

    async def get_id(self, category: str, subcategory: str | None = None) -> int | None:
        if self._current is None:
            return None
        id_ = await self._current.get_id(category, subcategory)
        if id_ is not None:
            return id_

        for source in self.sources:
            if source is self._current:
                continue
            if await source.get_id(category, subcategory) is not None:
                self._current = source
                return await source.get_id(category, subcategory)
        return None

    def has_ids(self, category: str, subcategory: str | None = None) -> bool:
        if self._current and self._current.has_ids(category, subcategory):
            return True
        return any(s.has_ids(category, subcategory) for s in self.sources)

    async def add_failed(self, category: str, id_: int, subcategory: str | None = None) -> None:
        for source in self.sources:
            if hasattr(source, "add_failed"):
                if asyncio.iscoroutinefunction(source.add_failed):
                    await source.add_failed(category, id_, subcategory)
                else:
                    source.add_failed(category, id_, subcategory)


def create_id_source(
    source_type: str,
    rc: RedisClient | None = None,
    id_ranges: dict | None = None,
    failed_id_store: FailedIdStore | None = None,
) -> IDSource:
    """Factory function to create an ID source by name."""
    if source_type == "archive":
        return ArchiveIDSource(pre_load=True)
    elif source_type == "top_players":
        return TopPlayerIDSource()
    elif source_type == "random":
        return RandomIDSource(id_ranges=id_ranges, failed_id_store=failed_id_store)
    else:  # "auto"
        return AutoIDSource(rc=rc, id_ranges=id_ranges, failed_id_store=failed_id_store)
