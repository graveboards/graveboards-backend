import asyncio
import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator, Optional

import httpx

from app.redis import RedisClient
from app.osu_api.client.osu_api_client import OsuAPIClient
from app.osu_api.enums import ScoreType, Ruleset

from .metadata_io import load_metadata, save_metadata, load_top_player_ids, save_top_player_ids
from .paths import get_fixture_path
from .constants import RULESETS, SCORE_TYPES, ID_RANGES
from .id_source import IDSource
from .validation import validate_data
from .progress import ProgressBar
from .failed_id_store import FailedIdStore
from app.exceptions import clean_error_msg

MAX_RETRIES = 10
MAX_RETRIES_SCORES = 50
RANKING_PAGE_SIZE = 50


class FetchEvent:
    def __init__(self, category: str, current: int, total: int):
        self.category = category
        self.current = current
        self.total = total


class FixtureDataFetcher:
    def __init__(self, rc: RedisClient, id_ranges: dict | None = None, force_fetch: bool = False,
                 id_source: IDSource | None = None, fixtures_dir: Path | None = None,
                 exclude_ids: list[int] | None = None, failed_id_store: FailedIdStore | None = None):
        self.rc = rc
        self.oac = OsuAPIClient(rc)
        self.logger = None
        self.force_fetch = force_fetch
        self.id_source = id_source
        self.fixtures_dir = fixtures_dir
        self.exclude_ids = set(exclude_ids) if exclude_ids else set()
        self.metadata = load_metadata(fixtures_dir=fixtures_dir)
        self.failed_id_store = failed_id_store or FailedIdStore(rc)
        self.id_ranges = id_ranges or self.metadata.get("id_ranges", ID_RANGES)
        self.top_player_ids = self.metadata.get("top_player_ids", {r: [] for r in RULESETS})
        self.last_fetch_results = {}
        self._current_session_results = {}
        self._valid_beatmap_ids: list[int] = []
        self._seen_ids: set[int] = set()
        self._consecutive_errors = 0
        self._failed_user_ids: list[int] = []
        self._scan_existing_fixtures()
        self._metadata_dirty = False

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
        for score_type in SCORE_TYPES:
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

    def _mark_metadata_dirty(self) -> None:
        """Mark metadata as dirty so it gets flushed later."""
        self._metadata_dirty = True

    def _flush_metadata(self) -> None:
        """Write metadata to disk if it has been modified."""
        if self._metadata_dirty:
            save_metadata(self.metadata, fixtures_dir=self.fixtures_dir)
            self._metadata_dirty = False

    def _check_connection_stability(self, error: Exception | None = None) -> None:
        """Fail fast when consecutive connection errors indicate a systemic issue
        (e.g. Redis unreachable, network down) rather than transient API errors.
        A connection-level failure won't resolve by retrying with a different ID.
        """
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
        """Write data to filepath atomically using tmp file + os.replace.
        
        Validates data if data_type is provided. Logs warning if invalid but still writes.
        """
        if data_type:
            is_valid, error_msg = validate_data(data, data_type)
            if not is_valid:
                self.logger.warning(f"Validation failed for {data_type}: {error_msg}")
        
        tmp_path = filepath.with_suffix(filepath.suffix + ".tmp")
        with open(tmp_path, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, filepath)

    async def fetch_beatmaps(self, count: int, skip_existing: bool = True) -> AsyncIterator[FetchEvent]:
        path = get_fixture_path("beatmaps", fixtures_dir=self.fixtures_dir)
        fetched = 0
        attempts = 0
        max_attempts = count * 10 if not self.force_fetch else count * 50

        while fetched < count and attempts < max_attempts:
            attempts += 1
            beatmap_id = await self._get_random_id("beatmaps", avoid_failed=False)

            if skip_existing and self._should_skip_id(beatmap_id):
                continue

            retries = 0
            inner_retries = MAX_RETRIES if not self.force_fetch else MAX_RETRIES_SCORES
            while retries < inner_retries:
                try:
                    data = await self.oac.get_beatmap(beatmap_id)
                    filepath = path / f"beatmap_{beatmap_id}.json"
                    self._atomic_write(filepath, data, "beatmap")
                    fetched += 1
                    self._valid_beatmap_ids.append(beatmap_id)
                    self._seen_ids.add(beatmap_id)
                    self._add_fetched_id("beatmaps", beatmap_id)
                    self._record_success()
                    self.logger.debug(f"Fetched beatmap {beatmap_id} ({fetched}/{count})")
                    break
                except Exception as e:
                    self._check_connection_stability(e)
                    if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 404:
                        self.logger.debug(f"Beatmap {beatmap_id} not found, skipping")
                        await self._add_failed_id("beatmaps", beatmap_id)
                        break
                    self.logger.debug(f"Failed to fetch beatmap {beatmap_id} (retry {retries + 1}/{inner_retries}): {clean_error_msg(e)}")
                    await self._add_failed_id("beatmaps", beatmap_id)
                    retries += 1
                    if retries < inner_retries:
                        beatmap_id = await self._get_random_id("beatmaps", avoid_failed=True)
            
            yield FetchEvent("beatmaps", fetched, count)

        if fetched < count:
            self.logger.warning(f"Only fetched {fetched}/{count} beatmaps")

        self.metadata["samples"]["beatmaps"]["count"] += fetched
        self.metadata["samples"]["beatmaps"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        self._mark_metadata_dirty()
        self._flush_metadata()
        self._current_session_results["beatmaps"] = fetched

    async def fetch_beatmapsets(self, count: int, skip_existing: bool = True) -> AsyncIterator[FetchEvent]:
        path = get_fixture_path("beatmapsets", fixtures_dir=self.fixtures_dir)
        fetched = 0
        attempts = 0
        max_attempts = count * 10 if not self.force_fetch else count * 50

        while fetched < count and attempts < max_attempts:
            attempts += 1
            beatmapset_id = await self._get_random_id("beatmapsets", avoid_failed=False)

            if skip_existing and self._should_skip_id(beatmapset_id):
                continue

            retries = 0
            inner_retries = MAX_RETRIES if not self.force_fetch else MAX_RETRIES_SCORES
            while retries < inner_retries:
                try:
                    data = await self.oac.get_beatmapset(beatmapset_id)
                    filepath = path / f"beatmapset_{beatmapset_id}.json"
                    self._atomic_write(filepath, data, "beatmapset")
                    fetched += 1
                    self._seen_ids.add(beatmapset_id)
                    self._add_fetched_id("beatmapsets", beatmapset_id)
                    self._record_success()
                    self.logger.debug(f"Fetched beatmapset {beatmapset_id} ({fetched}/{count})")
                    break
                except Exception as e:
                    self._check_connection_stability(e)
                    if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 404:
                        self.logger.debug(f"Beatmapset {beatmapset_id} not found, skipping")
                        await self._add_failed_id("beatmapsets", beatmapset_id)
                        break
                    self.logger.debug(f"Failed to fetch beatmapset {beatmapset_id} (retry {retries + 1}/{inner_retries}): {clean_error_msg(e)}")
                    await self._add_failed_id("beatmapsets", beatmapset_id)
                    retries += 1
                    if retries < inner_retries:
                        beatmapset_id = await self._get_random_id("beatmapsets", avoid_failed=True)
            
            yield FetchEvent("beatmapsets", fetched, count)

        if fetched < count:
            self.logger.warning(f"Only fetched {fetched}/{count} beatmapsets")

        self.metadata["samples"]["beatmapsets"]["count"] += fetched
        self.metadata["samples"]["beatmapsets"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        self._mark_metadata_dirty()
        self._flush_metadata()
        self._current_session_results["beatmapsets"] = fetched

    async def fetch_users(
        self,
        users_osu: int,
        users_taiko: int,
        users_fruits: int,
        users_mania: int,
        skip_existing: bool = True,
    ) -> AsyncIterator[FetchEvent]:
        path = get_fixture_path("users", fixtures_dir=self.fixtures_dir)
        fetched = {r: 0 for r in RULESETS}

        ruleset_counts = {
            "osu": users_osu,
            "taiko": users_taiko,
            "fruits": users_fruits,
            "mania": users_mania,
        }
        
        total_count = sum(ruleset_counts.values())
        cumulative_count = 0

        for ruleset in RULESETS:
            ruleset_path = path / ruleset
            ruleset_path.mkdir(parents=True, exist_ok=True)
            count = ruleset_counts[ruleset]
            attempts = 0
            max_attempts = count * 10 if not self.force_fetch else count * 50

            while fetched[ruleset] < count and attempts < max_attempts:
                attempts += 1
                user_id = await self._get_random_id(f"users.{ruleset}")

                if skip_existing and self._should_skip_id(user_id):
                    continue

                mode = getattr(Ruleset, ruleset.upper()).value
                retries = 0
                while retries < MAX_RETRIES:
                    try:
                        data = await self.oac.get_user(user_id, Ruleset(mode))
                        filepath = ruleset_path / f"user_{user_id}_{ruleset}.json"
                        self._atomic_write(filepath, data, "user")
                        fetched[ruleset] += 1
                        self._seen_ids.add(user_id)
                        self._add_fetched_id(f"users.{ruleset}", user_id)
                        self._record_success()
                        self.logger.debug(f"Fetched user {user_id} ({ruleset}) ({fetched[ruleset]}/{count})")
                        break
                    except Exception as e:
                        self._check_connection_stability(e)
                        if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 404:
                            self.logger.debug(f"User {user_id} ({ruleset}) not found, skipping")
                            await self._add_failed_id(f"users.{ruleset}", user_id)
                            break
                        self.logger.debug(f"Failed to fetch user {user_id} ({ruleset}) (retry {retries + 1}/{MAX_RETRIES}): {clean_error_msg(e)}")
                        await self._add_failed_id(f"users.{ruleset}", user_id)
                        retries += 1
                        user_id = await self._get_random_id(f"users.{ruleset}")

                cumulative_count += 1
                yield FetchEvent("users", cumulative_count, total_count)

        self.metadata["samples"]["users"]["count"] += sum(fetched.values())
        self.metadata["samples"]["users"]["per_ruleset"] = {
            r: self.metadata["samples"]["users"]["per_ruleset"].get(r, 0) + fetched[r] for r in RULESETS
        }
        self.metadata["samples"]["users"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        self._mark_metadata_dirty()
        self._flush_metadata()
        self._current_session_results["users"] = fetched.copy()

    async def fetch_users_by_ids(
        self,
        user_ids: list[int],
        ruleset: str = "osu",
    ) -> AsyncIterator[FetchEvent]:
        """Fetch specific users by their IDs (e.g., beatmapset owners)."""
        path = get_fixture_path("users", fixtures_dir=self.fixtures_dir)
        ruleset_path = path / ruleset
        ruleset_path.mkdir(parents=True, exist_ok=True)
        
        mode = getattr(Ruleset, ruleset.upper()).value
        fetched = 0
        total = len(user_ids)
        failed_ids: list[int] = []

        for user_id in user_ids:
            if self._should_skip_id(user_id):
                continue

            retries = 0
            while retries < MAX_RETRIES:
                try:
                    data = await self.oac.get_user(user_id, Ruleset(mode))
                    filepath = ruleset_path / f"user_{user_id}_{ruleset}.json"
                    self._atomic_write(filepath, data, "user")
                    fetched += 1
                    self._seen_ids.add(user_id)
                    self._add_fetched_id(f"users.{ruleset}", user_id)
                    self._record_success()
                    self.logger.debug(f"Fetched user {user_id} ({ruleset}) ({fetched}/{total})")
                    break
                except Exception as e:
                    self._check_connection_stability(e)
                    if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 404:
                        self.logger.warning(f"User {user_id} ({ruleset}) not found (404)")
                        await self._add_failed_id(f"users.{ruleset}", user_id)
                        failed_ids.append(user_id)
                        break
                    self.logger.debug(f"Failed to fetch user {user_id} ({ruleset}) (retry {retries + 1}/{MAX_RETRIES}): {clean_error_msg(e)}")
                    await self._add_failed_id(f"users.{ruleset}", user_id)
                    retries += 1

            yield FetchEvent("users", fetched, total)
        
        self._failed_user_ids = failed_ids

        self.metadata["samples"]["users"]["count"] += fetched
        self.metadata["samples"]["users"]["per_ruleset"] = {
            r: self.metadata["samples"]["users"]["per_ruleset"].get(r, 0) + (fetched if r == ruleset else 0) for r in RULESETS
        }
        self.metadata["samples"]["users"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        self._mark_metadata_dirty()
        self._flush_metadata()
        self._current_session_results["users"] = {r: (fetched if r == ruleset else 0) for r in RULESETS}
        self.last_fetch_results = {
            "beatmaps": 0,
            "beatmapsets": 0,
            "users": self._current_session_results["users"].copy(),
            "scores": {},
            "beatmap_scores": 0,
            "beatmap_attributes": 0,
        }

    async def fetch_scores(
        self,
        scores_best: int,
        scores_firsts: int,
        scores_recent: int,
        skip_existing: bool = True,
    ) -> AsyncIterator[FetchEvent]:
        if not self.top_player_ids.get(RULESETS[0]) or all(len(ids) == 0 for ids in self.top_player_ids.values()):
            self.logger.info("Top player IDs not found or empty. Fetching top players first...")
            await self.fetch_top_players()

        path = get_fixture_path("scores", fixtures_dir=self.fixtures_dir)
        fetched = {t: 0 for t in SCORE_TYPES}

        type_counts = {
            "best": scores_best,
            "firsts": scores_firsts,
            "recent": scores_recent,
        }

        total_count = sum(type_counts.values())
        cumulative_count = 0

        for score_type in SCORE_TYPES:
            type_path = path / score_type
            type_path.mkdir(parents=True, exist_ok=True)
            count = type_counts[score_type]
            attempts = 0
            max_attempts = count * 10 if not self.force_fetch else count * 50

            while fetched[score_type] < count and attempts < max_attempts:
                attempts += 1
                use_top_players = score_type in ["firsts", "recent"]
                user_id = await self._get_random_id("users", use_top_players=use_top_players)

                if skip_existing and self._should_skip_id(user_id):
                    continue

                mode = Ruleset.OSU
                score_type_enum = getattr(ScoreType, score_type.upper())
                retries = 0
                while retries < MAX_RETRIES:
                    try:
                        data = await self.oac.get_user_scores(user_id, score_type_enum, mode=mode)
                        if not isinstance(data, list) or not data:
                            self.logger.debug(f"Empty scores for user {user_id} ({score_type}) (retry {retries + 1}/{MAX_RETRIES})")
                            retries += 1
                            if retries >= MAX_RETRIES and score_type == "best":
                                user_id = await self._get_random_id("users", use_top_players=True)
                            else:
                                user_id = await self._get_random_id("users", use_top_players=use_top_players)
                            continue
                        filepath = type_path / f"scores_{user_id}_{score_type}.json"
                        self._atomic_write(filepath, data, "scores")
                        fetched[score_type] += 1
                        self._seen_ids.add(user_id)
                        self._add_fetched_id("users", user_id)
                        self._record_success()
                        self.logger.debug(f"Fetched scores for user {user_id} ({score_type}) ({fetched[score_type]}/{count})")
                        break
                    except Exception as e:
                        self._check_connection_stability(e)
                        if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 404:
                            self.logger.debug(f"User {user_id} not found for {score_type} scores, skipping")
                            await self._add_failed_id("users", user_id)
                            break
                        self.logger.debug(f"Failed to fetch scores for user {user_id} ({score_type}) (retry {retries + 1}/{MAX_RETRIES}): {clean_error_msg(e)}")
                        await self._add_failed_id("users", user_id)
                        retries += 1
                        if retries >= MAX_RETRIES and score_type == "best":
                            user_id = await self._get_random_id("users", use_top_players=True)
                        else:
                            user_id = await self._get_random_id("users", use_top_players=use_top_players)
                
                cumulative_count += 1
                yield FetchEvent("scores", cumulative_count, total_count)

        self.metadata["samples"]["scores"]["count"] += sum(fetched.values())
        self.metadata["samples"]["scores"]["per_type"] = {
            t: self.metadata["samples"]["scores"]["per_type"].get(t, 0) + fetched[t] for t in SCORE_TYPES
        }
        self.metadata["samples"]["scores"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        self._mark_metadata_dirty()
        self._flush_metadata()
        self._current_session_results["scores"] = fetched.copy()

    async def fetch_beatmap_scores(self, count: int, skip_existing: bool = True) -> AsyncIterator[FetchEvent]:
        path = get_fixture_path("beatmap_scores", fixtures_dir=self.fixtures_dir)
        fetched = 0
        valid_ids = list(self._valid_beatmap_ids)
        random.shuffle(valid_ids)
        valid_index = 0
        consecutive_empty = 0
        max_consecutive_empty = 50 if not self.force_fetch else 500

        for i in range(count):
            beatmap_id = None
            retries = 0
            inner_retries = MAX_RETRIES_SCORES if not self.force_fetch else 999999

            while retries < inner_retries:
                if valid_index < len(valid_ids):
                    beatmap_id = valid_ids[valid_index]
                    valid_index += 1
                else:
                    beatmap_id = await self._get_random_id("beatmaps", avoid_failed=True)

                if skip_existing and self._should_skip_id(beatmap_id):
                    continue

                try:
                    data = await self.oac.get_beatmap_scores(beatmap_id, limit=1)
                    scores = data.get("scores", [])
                    if not scores:
                        consecutive_empty += 1
                        if not self.force_fetch and consecutive_empty >= max_consecutive_empty:
                            self.logger.warning(f"Too many consecutive beatmaps with no scores ({consecutive_empty}), stopping beatmap_scores fetch")
                            break
                        retries += 1
                        continue
                    consecutive_empty = 0
                    self._record_success()
                    filepath = path / f"beatmap_scores_{beatmap_id}.json"
                    self._atomic_write(filepath, data, "beatmap_scores")
                    fetched += 1
                    self._seen_ids.add(beatmap_id)
                    self._add_fetched_id("beatmaps", beatmap_id)
                    self.logger.debug(f"Fetched beatmap scores {beatmap_id} ({fetched}/{count})")
                    break
                except Exception as e:
                    consecutive_empty = 0
                    self._check_connection_stability(e)
                    if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 404:
                        self.logger.debug(f"Beatmap {beatmap_id} not found for scores, skipping")
                        await self._add_failed_id("beatmaps", beatmap_id)
                        break
                    self.logger.debug(f"Failed to fetch beatmap scores {beatmap_id} (retry {retries + 1}/{inner_retries}): {clean_error_msg(e)}")
                    await self._add_failed_id("beatmaps", beatmap_id)
                    retries += 1

            yield FetchEvent("beatmap_scores", i + 1, count)

            if fetched >= count:
                break

        self.metadata["samples"]["beatmap_scores"]["count"] += fetched
        self.metadata["samples"]["beatmap_scores"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        self._mark_metadata_dirty()
        self._flush_metadata()
        self._current_session_results["beatmap_scores"] = fetched

    async def fetch_beatmap_attributes(self, count: int, skip_existing: bool = True) -> AsyncIterator[FetchEvent]:
        path = get_fixture_path("beatmap_attributes", fixtures_dir=self.fixtures_dir)
        fetched = 0
        valid_ids = list(self._valid_beatmap_ids)
        random.shuffle(valid_ids)
        valid_index = 0
        consecutive_errors = 0
        max_consecutive_errors = 50 if not self.force_fetch else 500

        for i in range(count):
            beatmap_id = None
            retries = 0
            inner_retries = MAX_RETRIES_SCORES if not self.force_fetch else 999999

            while retries < inner_retries:
                if valid_index < len(valid_ids):
                    beatmap_id = valid_ids[valid_index]
                    valid_index += 1
                else:
                    beatmap_id = await self._get_random_id("beatmaps", avoid_failed=True)

                if skip_existing and self._should_skip_id(beatmap_id):
                    continue

                mods = random.choice([0, 8, 16, 24, 64, 80])
                try:
                    data = await self.oac.get_beatmap_attributes(beatmap_id, mods)
                    consecutive_errors = 0
                    self._record_success()
                    filepath = path / f"beatmap_attrs_{beatmap_id}_mods{mods}.json"
                    self._atomic_write(filepath, data, "beatmap_attributes")
                    fetched += 1
                    self._seen_ids.add(beatmap_id)
                    self._add_fetched_id("beatmaps", beatmap_id)
                    self.logger.debug(f"Fetched beatmap attributes {beatmap_id} ({fetched}/{count})")
                    break
                except Exception as e:
                    consecutive_errors += 1
                    if not self.force_fetch and consecutive_errors >= max_consecutive_errors:
                        self.logger.warning(f"Too many consecutive beatmap attribute errors ({consecutive_errors}), stopping beatmap_attributes fetch")
                        break
                    self._check_connection_stability(e)
                    if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 404:
                        self.logger.debug(f"Beatmap {beatmap_id} not found for attributes, skipping")
                        await self._add_failed_id("beatmaps", beatmap_id)
                        break
                    self.logger.debug(f"Failed to fetch beatmap attributes {beatmap_id} (retry {retries + 1}/{inner_retries}): {clean_error_msg(e)}")
                    await self._add_failed_id("beatmaps", beatmap_id)
                    retries += 1

            yield FetchEvent("beatmap_attributes", i + 1, count)

            if fetched >= count:
                break

        self.metadata["samples"]["beatmap_attributes"]["count"] += fetched
        self.metadata["samples"]["beatmap_attributes"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        self._mark_metadata_dirty()
        self._flush_metadata()
        self._current_session_results["beatmap_attributes"] = fetched

    def refresh_top_player_ids_from_metadata(self) -> None:
        self.top_player_ids = self.metadata.get("top_player_ids", {r: [] for r in RULESETS})

    async def fetch_all(self, sample_counts: dict) -> AsyncIterator[FetchEvent]:
        self.last_fetch_results = {}
        self._current_session_results = {
            "beatmaps": 0,
            "beatmapsets": 0,
            "users": {r: 0 for r in RULESETS},
            "scores": {t: 0 for t in SCORE_TYPES},
            "beatmap_scores": 0,
            "beatmap_attributes": 0,
        }
        self._valid_beatmap_ids = []
        
        users = sample_counts.get("users", {})
        scores = sample_counts.get("scores", {})
        
        beatmaps_count = sample_counts.get("beatmaps", 0)
        beatmapsets_count = sample_counts.get("beatmapsets", 0)
        users_osu = users.get("osu", 0)
        users_taiko = users.get("taiko", 0)
        users_fruits = users.get("fruits", 0)
        users_mania = users.get("mania", 0)
        scores_best = scores.get("best", 0)
        scores_firsts = scores.get("firsts", 0)
        scores_recent = scores.get("recent", 0)
        beatmap_scores_count = sample_counts.get("beatmap_scores", 0)
        beatmap_attributes_count = sample_counts.get("beatmap_attributes", 0)
        
        if beatmaps_count > 0:
            async for event in self.fetch_beatmaps(beatmaps_count, skip_existing=True):
                yield event
        
        if beatmapsets_count > 0:
            async for event in self.fetch_beatmapsets(beatmapsets_count, skip_existing=True):
                yield event
        
        if users_osu > 0 or users_taiko > 0 or users_fruits > 0 or users_mania > 0:
            async for event in self.fetch_users(users_osu, users_taiko, users_fruits, users_mania, skip_existing=True):
                yield event
        
        if scores_best > 0 or scores_firsts > 0 or scores_recent > 0:
            async for event in self.fetch_scores(scores_best, scores_firsts, scores_recent, skip_existing=True):
                yield event
        
        if beatmap_scores_count > 0:
            async for event in self.fetch_beatmap_scores(beatmap_scores_count, skip_existing=True):
                yield event
        
        if beatmap_attributes_count > 0:
            async for event in self.fetch_beatmap_attributes(beatmap_attributes_count, skip_existing=True):
                yield event
        
        self.metadata = load_metadata(fixtures_dir=self.fixtures_dir)
        results = {
            "beatmaps": self._current_session_results["beatmaps"],
            "beatmapsets": self._current_session_results["beatmapsets"],
            "users": self._current_session_results["users"].copy(),
            "scores": self._current_session_results["scores"].copy(),
            "beatmap_scores": self._current_session_results["beatmap_scores"],
            "beatmap_attributes": self._current_session_results["beatmap_attributes"],
        }
        
        self.last_fetch_results = results

    async def fetch_top_players(
        self,
        rulesets: Optional[list[str]] = None,
        count_per_ruleset: int = 1000,
    ) -> dict[str, list[int]]:
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
                        ruleset=getattr(Ruleset, ruleset_name.upper()),
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
                    self.logger.error(f"Error fetching ranking for {ruleset_name}: {error_detail}")
                    break
            
            fetched[ruleset_name] = player_ids[:count_per_ruleset]
            self.logger.info(f"Fetched {len(player_ids)} top players for {ruleset_name}")
        
        current_top_ids = load_top_player_ids(fixtures_dir=self.fixtures_dir)
        current_top_ids.update(fetched)
        save_top_player_ids(current_top_ids, fixtures_dir=self.fixtures_dir)
        self.metadata = load_metadata(fixtures_dir=self.fixtures_dir)
        self.top_player_ids = self.metadata.get("top_player_ids", {r: [] for r in RULESETS})
        return fetched

    async def _get_random_id(self, category: str, use_top_players: bool = False, avoid_failed: bool = True) -> int:
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
            for _ in range(MAX_RETRIES * 3):
                candidate = random.randint(min_id, max_id)
                if not await self.failed_id_store.is_failed(category, candidate):
                    return candidate
        
        return random.randint(min_id, max_id)

    async def _add_failed_id(self, category: str, id_: int) -> None:
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
        fetched_ids = self.metadata.setdefault("fetched_ids", {
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
        
        self._mark_metadata_dirty()
