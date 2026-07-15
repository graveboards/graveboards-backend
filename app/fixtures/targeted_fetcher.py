import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator, Optional

from app.redis import RedisClient
from app.osu_api.client.osu_api_client import OsuAPIClient
from app.osu_api.enums import ScoreType, Ruleset

from .metadata_io import (
    load_metadata,
    save_metadata,
    load_top_player_ids,
    save_top_player_ids,
    create_targeted_metadata,
    get_fixture_count,
)
from .paths import get_fixture_path
from .constants import RULESETS, SCORE_TYPES, ID_RANGES, DISCUSSION_STATUSES
from .fetcher import FixtureDataFetcher, FetchEvent
from app.exceptions import clean_error_msg
from .id_source import IDSource


class TargetedFixtureFetcher(FixtureDataFetcher):
    """Enhanced fetcher with targeted coverage strategies.

    Provides fetch methods for specific criteria:
    - fetch_beatmapsets_by_status: Fetch by discussion status
    - fetch_beatmaps_by_difficulty: Fetch by difficulty range
    - fetch_beatmaps_by_playcount: Fetch by playcount range
    - fetch_users_by_activity: Fetch by activity level

    Each method has its own fetch loop with retry logic and metadata tracking.
    """

    def __init__(
        self,
        rc: RedisClient,
        id_ranges: dict | None = None,
        id_source: IDSource | None = None,
        fixtures_dir: Path | None = None,
        failed_id_store: FailedIdStore | None = None,
    ):
        super().__init__(
            rc,
            id_ranges,
            id_source=id_source,
            fixtures_dir=fixtures_dir,
            failed_id_store=failed_id_store,
        )
        # Difficulty and playcount categorization uses Categorizer instances from categorization.py
        self.activity_levels = ["active", "moderate", "inactive"]

    async def fetch_beatmapsets_by_status(
        self,
        status: str = "ranked",
        count: int = 10,
        skip_existing: bool = True,
    ) -> AsyncIterator[FetchEvent]:
        """Fetch beatmapsets by status using discussions endpoint."""
        path = get_fixture_path("beatmapsets", fixtures_dir=self.fixtures_dir)
        fetched = 0
        page = 1
        fetched_ids = set()

        while fetched < count:
            try:
                data = await self.oac.get_beatmapset_discussions(
                    beatmapset_status=status,
                    page=page,
                    limit=50,
                )

                discussions = data.get("discussions", [])
                if not discussions:
                    break

                for discussion in discussions:
                    if fetched >= count:
                        break

                    beatmapset_id = discussion.get("beatmapset_id")
                    if not beatmapset_id or beatmapset_id in fetched_ids:
                        continue

                    if skip_existing and beatmapset_id in self._seen_ids:
                        fetched_ids.add(beatmapset_id)
                        continue

                    try:
                        beatmapset_data = await self.oac.get_beatmapset(beatmapset_id)
                        filepath = path / f"beatmapset_{beatmapset_id}.json"
                        with open(filepath, "w") as f:
                            json.dump(beatmapset_data, f, indent=2)

                        fetched += 1
                        fetched_ids.add(beatmapset_id)
                        self._seen_ids.add(beatmapset_id)
                        self.logger.debug(
                            f"Fetched beatmapset {beatmapset_id} (status={status}) "
                            f"({fetched}/{count})"
                        )

                        self._update_beatmapset_metadata(beatmapset_data)

                    except Exception as e:
                        self.logger.debug(
                            f"Failed to fetch beatmapset {beatmapset_id}: {clean_error_msg(e)}"
                        )
                        await self._add_failed_id("beatmapsets", beatmapset_id)

                page += 1

                if len(discussions) < 50:
                    break

            except Exception as e:
                self.logger.error(f"Error fetching discussions for status={status}: {e}")
                break

        self.metadata["samples"]["beatmapsets"]["count"] += fetched
        self.metadata["samples"]["beatmapsets"]["last_fetched"] = datetime.now(
            timezone.utc
        ).isoformat()
        save_metadata(self.metadata, fixtures_dir=self.fixtures_dir)
        self._current_session_results["beatmapsets"] = fetched

        for i in range(count):
            yield FetchEvent("beatmapsets", i + 1, count)

    async def fetch_beatmaps_by_difficulty(
        self,
        ruleset: str = "osu",
        difficulty_range: str = "medium",
        count: int = 10,
        skip_existing: bool = True,
    ) -> AsyncIterator[FetchEvent]:
        """Fetch beatmaps within difficulty range."""
        path = get_fixture_path("beatmaps", fixtures_dir=self.fixtures_dir)
        fetched = 0

        if ruleset not in RULESETS:
            self.logger.warning(f"Invalid ruleset: {ruleset}")
            return

        min_diff, max_diff = self.difficulty_ranges.get(
            difficulty_range, self.difficulty_ranges["medium"]
        )

        await self.fetch_top_players(rulesets=[ruleset], count_per_ruleset=500)

        attempts = 0
        max_attempts = count * 10

        while fetched < count and attempts < max_attempts:
            attempts += 1
            use_top_players = attempts % 3 != 0
            user_id = await self._get_random_id(
                "users", use_top_players=use_top_players, avoid_failed=True
            )
            mode = getattr(Ruleset, ruleset.upper()).value

            try:
                beatmaps_data = await self.oac.get_user(user_id, mode=mode)
                user_beatmaps = beatmaps_data.get("beatmaps", [])

                for beatmap in user_beatmaps:
                    if fetched >= count:
                        break

                    beatmap_id = beatmap.get("id")
                    if not beatmap_id:
                        continue

                    if skip_existing and beatmap_id in self._seen_ids:
                        continue

                    diff = beatmap.get("difficulty_rating", 0)
                    if not (min_diff <= diff <= max_diff):
                        continue

                    try:
                        beatmap_data = await self.oac.get_beatmap(beatmap_id)
                        filepath = path / f"beatmap_{beatmap_id}.json"
                        with open(filepath, "w") as f:
                            json.dump(beatmap_data, f, indent=2)

                        fetched += 1
                        self._seen_ids.add(beatmap_id)
                        self.logger.debug(
                            f"Fetched beatmap {beatmap_id} (difficulty={diff}) "
                            f"({fetched}/{count})"
                        )

                        self._update_beatmap_metadata(beatmap_data)

                        if fetched >= count:
                            break

                    except Exception as e:
                        self.logger.debug(
                            f"Failed to fetch beatmap {beatmap_id}: {clean_error_msg(e)}"
                        )
                        await self._add_failed_id("beatmaps", beatmap_id)

                if fetched >= count:
                    break

            except Exception as e:
                self.logger.debug(f"Error fetching user {user_id}: {e}")
                continue

        if fetched < count:
            self.logger.warning(
                f"Only fetched {fetched}/{count} beatmaps for difficulty {difficulty_range}"
            )

        self.metadata["samples"]["beatmaps"]["count"] += fetched
        self.metadata["samples"]["beatmaps"]["last_fetched"] = datetime.now(
            timezone.utc
        ).isoformat()
        save_metadata(self.metadata, fixtures_dir=self.fixtures_dir)
        self._current_session_results["beatmaps"] = fetched

        for i in range(count):
            yield FetchEvent("beatmaps", i + 1, count)

    async def fetch_users_by_activity(
        self,
        ruleset: str,
        activity_level: str = "active",
        count: int = 25,
        skip_existing: bool = True,
    ) -> AsyncIterator[FetchEvent]:
        """Fetch users with specified activity level."""
        path = get_fixture_path("users", fixtures_dir=self.fixtures_dir)
        ruleset_path = path / ruleset
        ruleset_path.mkdir(parents=True, exist_ok=True)
        fetched = 0

        if activity_level not in self.activity_levels:
            self.logger.warning(f"Invalid activity level: {activity_level}")
            return

        await self.fetch_top_players(rulesets=[ruleset], count_per_ruleset=1000)

        top_players = self.top_player_ids.get(ruleset, [])
        random.shuffle(top_players)

        for user_id in top_players:
            if fetched >= count:
                break

            if skip_existing and user_id in self._seen_ids:
                continue

            mode = getattr(Ruleset, ruleset.upper()).value

            try:
                user_data = await self.oac.get_user(user_id, mode=mode)
                filepath = ruleset_path / f"user_{user_id}_{ruleset}.json"
                with open(filepath, "w") as f:
                    json.dump(user_data, f, indent=2)

                fetched += 1
                self._seen_ids.add(user_id)
                self.logger.debug(
                    f"Fetched user {user_id} ({ruleset}, {activity_level}) " f"({fetched}/{count})"
                )

                self._update_user_metadata(user_data, ruleset, activity_level)

            except Exception as e:
                self.logger.debug(f"Failed to fetch user {user_id}: {clean_error_msg(e)}")
                await self._add_failed_id(f"users.{ruleset}", user_id)

        if fetched < count:
            self.logger.warning(
                f"Only fetched {fetched}/{count} users for {ruleset} {activity_level}"
            )

        self.metadata["samples"]["users"]["count"] += fetched
        self.metadata["samples"]["users"]["per_ruleset"][ruleset] = (
            self.metadata["samples"]["users"]["per_ruleset"].get(ruleset, 0) + fetched
        )
        self.metadata["samples"]["users"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        save_metadata(self.metadata, fixtures_dir=self.fixtures_dir)
        self._current_session_results["users"] = {ruleset: fetched}

        for i in range(count):
            yield FetchEvent("users", i + 1, count)

    async def fetch_beatmaps_by_playcount(
        self,
        playcount_range: str = "medium",
        count: int = 10,
        skip_existing: bool = True,
    ) -> AsyncIterator[FetchEvent]:
        """Fetch beatmaps within playcount range."""
        path = get_fixture_path("beatmaps", fixtures_dir=self.fixtures_dir)
        fetched = 0

        min_pc, max_pc = self.playcount_ranges.get(playcount_range, self.playcount_ranges["medium"])

        attempts = 0
        max_attempts = count * 10

        while fetched < count and attempts < max_attempts:
            attempts += 1
            beatmap_id = await self._get_random_id("beatmaps", avoid_failed=True)

            if skip_existing and beatmap_id in self._seen_ids:
                continue

            try:
                beatmap_data = await self.oac.get_beatmap(beatmap_id)
                playcount = beatmap_data.get("playcount", 0)

                if not (min_pc <= playcount <= max_pc):
                    continue

                filepath = path / f"beatmap_{beatmap_id}.json"
                with open(filepath, "w") as f:
                    json.dump(beatmap_data, f, indent=2)

                fetched += 1
                self._seen_ids.add(beatmap_id)
                self.logger.debug(
                    f"Fetched beatmap {beatmap_id} (playcount={playcount}) " f"({fetched}/{count})"
                )

                self._update_beatmap_metadata(beatmap_data)

                if fetched >= count:
                    break

            except Exception as e:
                self.logger.debug(f"Failed to fetch beatmap {beatmap_id}: {e}")
                await self._add_failed_id("beatmaps", beatmap_id)

        if fetched < count:
            self.logger.warning(
                f"Only fetched {fetched}/{count} beatmaps for playcount {playcount_range}"
            )

        self.metadata["samples"]["beatmaps"]["count"] += fetched
        self.metadata["samples"]["beatmaps"]["last_fetched"] = datetime.now(
            timezone.utc
        ).isoformat()
        save_metadata(self.metadata, fixtures_dir=self.fixtures_dir)
        self._current_session_results["beatmaps"] = fetched

        for i in range(count):
            yield FetchEvent("beatmaps", i + 1, count)

    async def fetch_all_targeted(
        self,
        counts: dict,
    ) -> AsyncIterator[FetchEvent]:
        """Fetch fixtures with targeted coverage."""
        self.last_fetch_results = {}
        self._current_session_results = {
            "beatmaps": 0,
            "beatmapsets": 0,
            "users": {r: 0 for r in RULESETS},
            "scores": {t: 0 for t in SCORE_TYPES},
            "beatmap_scores": 0,
            "beatmap_attributes": 0,
        }

        beatmaps_targeted = counts.get("beatmaps", {})
        beatmapsets_targeted = counts.get("beatmapsets", {})
        users_targeted = counts.get("users", {})
        scores_targeted = counts.get("scores", {})

        beatmaps_count = beatmaps_targeted.get("total", 0)
        beatmapsets_count = beatmapsets_targeted.get("total", 0)

        if beatmaps_targeted.get("by_status"):
            for status, status_count in beatmaps_targeted["by_status"].items():
                if status_count > 0:
                    async for event in self.fetch_beatmapsets_by_status(
                        status=status,
                        count=status_count,
                        skip_existing=True,
                    ):
                        yield event

        if beatmaps_targeted.get("by_difficulty"):
            for difficulty, diff_count in beatmaps_targeted["by_difficulty"].items():
                if diff_count > 0:
                    for ruleset in RULESETS:
                        async for event in self.fetch_beatmaps_by_difficulty(
                            ruleset=ruleset,
                            difficulty_range=difficulty,
                            count=diff_count,
                            skip_existing=True,
                        ):
                            yield event

        if beatmaps_targeted.get("by_playcount"):
            for playcount, pc_count in beatmaps_targeted["by_playcount"].items():
                if pc_count > 0:
                    async for event in self.fetch_beatmaps_by_playcount(
                        playcount_range=playcount,
                        count=pc_count,
                        skip_existing=True,
                    ):
                        yield event

        if users_targeted.get("by_activity"):
            for activity, activity_counts in users_targeted["by_activity"].items():
                for ruleset in RULESETS:
                    activity_count = activity_counts.get(ruleset, 0)
                    if activity_count > 0:
                        async for event in self.fetch_users_by_activity(
                            ruleset=ruleset,
                            activity_level=activity,
                            count=activity_count,
                            skip_existing=True,
                        ):
                            yield event

        if beatmapsets_count > 0 and not beatmaps_targeted.get("by_status"):
            async for event in super().fetch_beatmapsets(beatmapsets_count, skip_existing=True):
                yield event

        if beatmaps_count > 0 and not beatmaps_targeted.get("by_difficulty"):
            async for event in super().fetch_beatmaps(beatmaps_count, skip_existing=True):
                yield event

        self.metadata = load_metadata()
        results = {
            "beatmaps": self._current_session_results["beatmaps"],
            "beatmapsets": self._current_session_results["beatmapsets"],
            "users": self._current_session_results["users"].copy(),
            "scores": self._current_session_results["scores"].copy(),
            "beatmap_scores": self._current_session_results["beatmap_scores"],
            "beatmap_attributes": self._current_session_results["beatmap_attributes"],
        }

        self.last_fetch_results = results

    def _update_beatmap_metadata(self, beatmap_data: dict):
        """Update targeted metadata for a beatmap."""
        beatmap_id = beatmap_data.get("id")
        if not beatmap_id:
            return

        if "targeted" not in self.metadata:
            self._init_metadata()

        if "beatmaps" not in self.metadata["targeted"]:
            self.metadata["targeted"]["beatmaps"] = {
                "by_status": {},
                "by_ruleset": {},
                "by_difficulty": {},
                "by_playcount": {},
                "file_metadata": {},
            }

        beatmaps_meta = self.metadata["targeted"]["beatmaps"]
        file_meta = beatmaps_meta.setdefault("file_metadata", {})

        file_meta[str(beatmap_id)] = {
            "filepath": str(
                get_fixture_path("beatmaps", fixtures_dir=self.fixtures_dir)
                / f"beatmap_{beatmap_id}.json"
            ),
            "status": beatmap_data.get("status"),
            "ruleset": "osu",
            "difficulty_rating": beatmap_data.get("difficulty_rating", 0),
            "playcount": beatmap_data.get("playcount", 0),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

        self._update_status_metadata(beatmaps_meta, beatmap_data)
        self._update_difficulty_metadata(beatmaps_meta, beatmap_data)
        self._update_playcount_metadata(beatmaps_meta, beatmap_data)

        save_metadata(self.metadata, fixtures_dir=self.fixtures_dir)

    def _update_beatmapset_metadata(self, beatmapset_data: dict):
        """Update targeted metadata for a beatmapset."""
        beatmapset_id = beatmapset_data.get("id")
        if not beatmapset_id:
            return

        if "targeted" not in self.metadata:
            self._init_metadata()

        if "beatmapsets" not in self.metadata["targeted"]:
            self.metadata["targeted"]["beatmapsets"] = {
                "by_status": {},
                "file_metadata": {},
            }

        beatmapsets_meta = self.metadata["targeted"]["beatmapsets"]
        file_meta = beatmapsets_meta.setdefault("file_metadata", {})

        file_meta[str(beatmapset_id)] = {
            "filepath": str(
                get_fixture_path("beatmapsets", fixtures_dir=self.fixtures_dir)
                / f"beatmapset_{beatmapset_id}.json"
            ),
            "status": beatmapset_data.get("status"),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

        self._update_status_metadata(beatmapsets_meta, beatmapset_data)

        save_metadata(self.metadata, fixtures_dir=self.fixtures_dir)

    def _update_user_metadata(
        self,
        user_data: dict,
        ruleset: str,
        activity_level: str = "active",
    ):
        """Update targeted metadata for a user."""
        user_id = user_data.get("id")
        if not user_id:
            return

        if "targeted" not in self.metadata:
            self._init_metadata()

        if "users" not in self.metadata["targeted"]:
            self.metadata["targeted"]["users"] = {
                "by_activity": {},
                "per_ruleset": {},
                "file_metadata": {},
            }

        users_meta = self.metadata["targeted"]["users"]
        file_meta = users_meta.setdefault("file_metadata", {})

        file_meta[str(user_id)] = {
            "filepath": str(
                get_fixture_path("users", fixtures_dir=self.fixtures_dir)
                / ruleset
                / f"user_{user_id}_{ruleset}.json"
            ),
            "activity_level": activity_level,
            "ruleset": ruleset,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

        activity_meta = users_meta.setdefault("by_activity", {})
        if activity_level not in activity_meta:
            activity_meta[activity_level] = {r: 0 for r in RULESETS}
        activity_meta[activity_level][ruleset] = activity_meta[activity_level].get(ruleset, 0) + 1

        ruleset_meta = users_meta.setdefault("per_ruleset", {})
        if ruleset not in ruleset_meta:
            ruleset_meta[ruleset] = {l: 0 for l in self.activity_levels}
        ruleset_meta[ruleset][activity_level] = ruleset_meta[ruleset].get(activity_level, 0) + 1

        save_metadata(self.metadata, fixtures_dir=self.fixtures_dir)

    def _update_status_metadata(self, category_meta: dict, data: dict):
        """Update status counts in metadata."""
        status = data.get("status")
        if not status:
            return

        by_status = category_meta.setdefault("by_status", {})
        by_status[status] = by_status.get(status, 0) + 1

    def _update_difficulty_metadata(self, category_meta: dict, data: dict):
        """Update difficulty counts in metadata."""
        diff = data.get("difficulty_rating", 0)
        if diff is None:
            return

        difficulty = self._categorize_difficulty(diff)
        by_difficulty = category_meta.setdefault("by_difficulty", {})
        by_difficulty[difficulty] = by_difficulty.get(difficulty, 0) + 1

    def _update_playcount_metadata(self, category_meta: dict, data: dict):
        """Update playcount counts in metadata."""
        playcount = data.get("playcount", 0)
        if playcount is None:
            return

        playcount_cat = self._categorize_playcount(playcount)
        by_playcount = category_meta.setdefault("by_playcount", {})
        by_playcount[playcount_cat] = by_playcount.get(playcount_cat, 0) + 1

    def _categorize_difficulty(self, difficulty: float) -> str:
        """Categorize difficulty rating using half-open intervals."""
        from .categorization import DIFFICULTY_CATEGORIZER

        return DIFFICULTY_CATEGORIZER.categorize(difficulty) or "expert"

    def _categorize_playcount(self, playcount: int) -> str:
        """Categorize playcount using half-open intervals."""
        from .categorization import PLAYCOUNT_CATEGORIZER

        return PLAYCOUNT_CATEGORIZER.categorize(playcount) or "high"

    def _init_metadata(self):
        """Initialize targeted metadata structure."""
        if "targeted" not in self.metadata:
            self.metadata["targeted"] = create_targeted_metadata()

    def set_targeted_fetch(
        self,
        statuses: list[str] | None = None,
        difficulty_range: str | None = None,
        playcount_range: str | None = None,
        activity_tier: str | None = None,
        rulesets: list[str] | None = None,
    ):
        """Configure targeted fetching parameters."""
        self.targeted_statuses = statuses
        self.targeted_difficulty_range = difficulty_range
        self.targeted_playcount_range = playcount_range
        self.targeted_activity_tier = activity_tier
        self.targeted_rulesets = rulesets if rulesets else ["osu"]

    def get_last_results(self) -> dict:
        """Get last fetch results for CLI output."""
        results = {
            "beatmaps": {"count": 0, "last_fetched": None},
            "beatmapsets": {"count": 0, "last_fetched": None},
            "users": {"count": 0, "per_ruleset": {r: 0 for r in RULESETS}, "last_fetched": None},
            "scores": {"count": 0, "per_type": {t: 0 for t in SCORE_TYPES}, "last_fetched": None},
            "beatmap_scores": {"count": 0, "last_fetched": None},
            "beatmap_attributes": {"count": 0, "last_fetched": None},
        }

        if self.targeted_statuses:
            results["beatmapsets"]["count"] = sum(
                self.metadata.get("targeted", {})
                .get("beatmapsets", {})
                .get("by_status", {})
                .get(status, 0)
                for status in self.targeted_statuses
            )

        if self.targeted_difficulty_range:
            results["beatmaps"]["count"] = (
                self.metadata.get("targeted", {})
                .get("beatmaps", {})
                .get("by_difficulty", {})
                .get(self.targeted_difficulty_range, 0)
            )

        if self.targeted_activity_tier:
            users_meta = self.metadata.get("targeted", {}).get("users", {})
            per_ruleset = users_meta.get("per_ruleset", {})
            for r in self.targeted_rulesets:
                count = per_ruleset.get(r, {}).get(self.targeted_activity_tier, 0)
                results["users"]["count"] += count
                results["users"]["per_ruleset"][r] = count

        return results

    async def fetch_targeted(self):
        """Execute targeted fetch based on configured parameters."""
        counts = {
            "beatmapsets": {},
            "beatmaps": {},
            "users": {},
        }

        if self.targeted_statuses:
            counts["beatmapsets"]["by_status"] = {status: 10 for status in self.targeted_statuses}

        if self.targeted_difficulty_range:
            counts["beatmaps"]["by_difficulty"] = {self.targeted_difficulty_range: 10}

        if self.targeted_playcount_range:
            counts["beatmaps"]["by_playcount"] = {self.targeted_playcount_range: 10}

        if self.targeted_activity_tier:
            counts["users"]["by_activity"] = {
                self.targeted_activity_tier: {ruleset: 10 for ruleset in self.targeted_rulesets}
            }

        if not any(counts.values()):
            self.logger.warning(
                "No targeted criteria specified. "
                "Use --status, --difficulty-range, --playcount-range, or --activity-tier. "
                "Returning without fetching."
            )
            return

        async for event in self.fetch_all_targeted(counts):
            yield event
