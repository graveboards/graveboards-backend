"""Base fetcher with shared logic for all fetcher types.

Extracts common functionality from FixtureDataFetcher that is shared across
standard, targeted, and search-test fetchers.
"""

import asyncio
import json
import os
import random
from pathlib import Path
from typing import Optional

from app.redis import RedisClient
from app.osu_api.client.osu_api_client import OsuAPIClient
from app.osu_api.enums import Ruleset

from .paths import get_fixture_path
from .metadata_io import load_metadata, save_metadata, load_top_player_ids
from .constants import RULESETS, ID_RANGES
from .failed_id_store import FailedIdStore
from .id_source import IDSource
from .validation import validate_data
from app.exceptions import clean_error_msg


class BaseFetcher:
    """Base class with shared fetcher functionality.

    Subclasses implement fetch_one() for their specific data type.
    """

    def __init__(
        self,
        rc: RedisClient,
        id_ranges: dict | None = None,
        id_source: IDSource | None = None,
        fixtures_dir: Path | None = None,
        failed_id_store: FailedIdStore | None = None,
    ):
        self.rc = rc
        self.oac = OsuAPIClient(rc)
        self.logger = None
        self.force_fetch = False
        self.id_source = id_source
        self.fixtures_dir = fixtures_dir
        self.exclude_ids = set()
        self.failed_id_store = failed_id_store or FailedIdStore(rc)
        self.id_ranges = id_ranges or ID_RANGES
        self.top_player_ids = load_top_player_ids(fixtures_dir=fixtures_dir)
        self._seen_ids: set[int] = set()
        self._valid_beatmap_ids: list[int] = []
        self._consecutive_errors = 0
        self._scan_existing_fixtures()

    def _scan_existing_fixtures(self) -> None:
        """Scan existing fixture files and populate _seen_ids."""
        for category in ["beatmaps", "beatmapsets"]:
            path = get_fixture_path(category, fixtures_dir=self.fixtures_dir)
            for f in path.glob(f"{category}_*.json"):
                try:
                    id_str = f.stem.replace(f"{category}_", "")
                    self._seen_ids.add(int(id_str))
                except ValueError:
                    continue

        for ruleset in RULESETS:
            path = get_fixture_path("users", fixtures_dir=self.fixtures_dir) / ruleset
            for f in path.glob("user_*.json"):
                try:
                    parts = f.stem.split("_")
                    if len(parts) >= 2:
                        self._seen_ids.add(int(parts[1]))
                except ValueError:
                    continue

        for score_type in ["best", "firsts", "recent"]:
            path = get_fixture_path("scores", fixtures_dir=self.fixtures_dir) / score_type
            for f in path.glob("scores_*.json"):
                try:
                    parts = f.stem.split("_")
                    if len(parts) >= 2:
                        self._seen_ids.add(int(parts[1]))
                except ValueError:
                    continue

        self._seen_ids.update(self.exclude_ids)

    def _should_skip_id(self, id_: int) -> bool:
        """Check if an ID should be skipped (seen, failed, or excluded)."""
        if id_ in self._seen_ids:
            return True
        if id_ in self.exclude_ids:
            return True
        return False

    def _check_connection_stability(self, error: Exception | None = None) -> None:
        """Fail fast when consecutive connection errors indicate a systemic issue."""
        import httpx
        if error is not None and isinstance(error, httpx.HTTPStatusError):
            return
        self._consecutive_errors += 1
        if self._consecutive_errors >= 5:
            raise ConnectionError(
                f"Consecutive connection errors ({self._consecutive_errors}) — "
                f"service appears unreachable. Aborting fetch."
            )

    def _record_success(self) -> None:
        """Reset the consecutive error counter on a successful fetch."""
        self._consecutive_errors = 0

    def _atomic_write(self, filepath: Path, data: dict, data_type: str = "") -> None:
        """Write data to filepath atomically using tmp file + os.replace."""
        if data_type:
            is_valid, error_msg = validate_data(data, data_type)
            if not is_valid and self.logger:
                self.logger.warning(f"Validation failed for {data_type}: {error_msg}")

        tmp_path = filepath.with_suffix(filepath.suffix + ".tmp")
        with open(tmp_path, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, filepath)

    async def _get_random_id(
        self,
        category: str,
        use_top_players: bool = False,
        avoid_failed: bool = True,
    ) -> int:
        """Get a random ID for fetching, trying ID source first then falling back to random."""
        if self.id_source:
            subcategory = None
            if category.startswith("users."):
                subcategory = category.split(".", 1)[1]
            id_ = await self.id_source.get_id(category, subcategory)
            if id_ is not None:
                return id_

        if use_top_players and category == "users" and self.top_player_ids:
            for ruleset in RULESETS:
                top_ids = self.top_player_ids.get(ruleset, [])
                if top_ids:
                    if avoid_failed:
                        for candidate in top_ids:
                            if not await self.failed_id_store.is_failed("users", candidate, ruleset):
                                return candidate
                    else:
                        return random.choice(top_ids)

        range_config = self.id_ranges.get(category, self.id_ranges.get(category.split(".")[0], {"min": 1, "max": 1000000}))
        min_id = range_config.get("min", 1)
        max_id = range_config.get("max", 1000000)

        if avoid_failed:
            for _ in range(30):
                candidate = random.randint(min_id, max_id)
                if not await self.failed_id_store.is_failed(category, candidate):
                    return candidate

        return random.randint(min_id, max_id)

    async def _add_failed_id(self, category: str, id_: int) -> None:
        """Add an ID to the failed set."""
        subcategory = None
        if category.startswith("users."):
            subcategory = category.split(".", 1)[1]
        await self.failed_id_store.add_failed(category, id_, subcategory)

        if self.id_source and hasattr(self.id_source, "add_failed"):
            if asyncio.iscoroutinefunction(self.id_source.add_failed):
                await self.id_source.add_failed(category, id_, subcategory)
            else:
                self.id_source.add_failed(category, id_, subcategory)

    def _add_fetched_id(self, category: str, id_: int) -> None:
        """Track a successfully fetched ID in metadata."""
        metadata = load_metadata(fixtures_dir=self.fixtures_dir)
        fetched_ids = metadata.setdefault("fetched_ids", {
            "beatmaps": [],
            "beatmapsets": [],
            "users": {r: [] for r in RULESETS},
        })

        if category not in fetched_ids:
            fetched_ids[category] = []

        category_ids = fetched_ids[category]

        if isinstance(category_ids, dict):
            for subcategory in category_ids.values():
                if id_ not in subcategory:
                    subcategory.append(id_)
                    if len(subcategory) > 10000:
                        subcategory[:] = subcategory[-10000:]
        else:
            if id_ not in category_ids:
                category_ids.append(id_)
                if len(category_ids) > 10000:
                    category_ids[:] = category_ids[-10000:]

        metadata["last_updated"] = None  # Will be set by save_metadata
        save_metadata(metadata, fixtures_dir=self.fixtures_dir)

    async def fetch_top_players(
        self,
        rulesets: list[str] | None = None,
        count_per_ruleset: int = 1000,
    ) -> dict[str, list[int]]:
        """Fetch top player IDs from osu! API rankings."""
        from .constants import RANKING_PAGE_SIZE
        from app.osu_api.enums import Ruleset as RulesetEnum

        if rulesets is None:
            rulesets = RULESETS

        fetched = {}

        for ruleset_name in rulesets:
            page = 1
            player_ids = []

            while len(player_ids) < count_per_ruleset:
                remaining = count_per_ruleset - len(player_ids)
                limit = min(RANKING_PAGE_SIZE, remaining)

                try:
                    data = await self.oac.get_rankings(
                        ruleset=getattr(RulesetEnum, ruleset_name.upper()),
                        mode="performance",
                        cursor_page=page,
                        limit=limit
                    )

                    players = data.get("ranking", [])
                    if not players:
                        break

                    for player in players:
                        user = player.get("user")
                        if user and "id" in user:
                            player_ids.append(user["id"])

                    if len(players) < limit:
                        break

                    page += 1

                except Exception as e:
                    error_detail = f"{type(e).__name__}: {e}"
                    if hasattr(e, "response") and e.response is not None:
                        try:
                            error_detail += f" (status={e.response.status_code}, body={e.response.text[:200]})"
                        except Exception:
                            pass
                    if self.logger:
                        self.logger.error(f"Error fetching ranking for {ruleset_name}: {error_detail}")
                    break

            fetched[ruleset_name] = player_ids[:count_per_ruleset]
            if self.logger:
                self.logger.info(f"Fetched {len(player_ids)} top players for {ruleset_name}")

        # Save to metadata
        current_top_ids = load_top_player_ids(fixtures_dir=self.fixtures_dir)
        current_top_ids.update(fetched)
        save_metadata(load_metadata(fixtures_dir=self.fixtures_dir), fixtures_dir=self.fixtures_dir)
        self.top_player_ids = current_top_ids

        return fetched
