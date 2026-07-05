"""Coverage-gated fetcher for comprehensive search engine test coverage.

Uses random fetch + multi-bucket classification to efficiently populate
all searchable field coverage with minimal API calls. One API call can
fill 10+ coverage buckets simultaneously.

Usage:
    fetcher = SearchTestFixtureFetcher(rc)
    report = await fetcher.ensure_search_test_coverage(
        min_per_category=1,
        max_total=500,
    )
"""
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.redis import RedisClient
from app.osu_api.client.osu_api_client import OsuAPIClient
from app.osu_api.enums import Ruleset

from .utils import (
    load_metadata,
    save_metadata,
    get_fixture_path,
    load_top_player_ids,
    save_top_player_ids,
)
from .fetcher import FixtureDataFetcher, FetchEvent
from .id_source import IDSource
from .search_test_constants import (
    GENRE_IDS,
    GENRE_NAMES,
    LANGUAGE_IDS,
    LANGUAGE_NAMES,
    COUNTRY_CODES,
    BEATMAP_STATUSES,
    BEATMAP_STATUS_NAMES,
    BEATMAP_MODES,
    BEATMAP_MODE_NAMES,
)
from .search_test_known_ids import (
    RESTRICTED_BEATMAPSET_IDS,
    NSFW_BEATMAPSET_IDS,
)

# BPM ranges for categorization
BPM_RANGES = {
    "low": (0, 90),
    "medium": (90, 150),
    "high": (150, 9999),
}

# Accuracy ranges (0-100%)
ACCURACY_RANGES = {
    "low": (0, 80),
    "medium": (80, 95),
    "high": (95, 100.01),
}

# Hit length ranges (seconds)
HIT_LENGTH_RANGES = {
    "short": (0, 60),
    "medium": (60, 180),
    "long": (180, 99999),
}

# Max combo ranges
MAX_COMBO_RANGES = {
    "low": (0, 500),
    "medium": (500, 1500),
    "high": (1500, 9999999),
}

# Drain ranges (AR-like, 0-10)
DRAIN_RANGES = {
    "low": (0, 3.0),
    "medium": (3.0, 6.0),
    "high": (6.0, 99.0),
}

# AR ranges (Approach Rate, 0-10)
AR_RANGES = {
    "low": (0, 3.0),
    "medium": (3.0, 6.0),
    "high": (6.0, 99.0),
}

# CS ranges (Circle Size, 0-10)
CS_RANGES = {
    "low": (0, 3.0),
    "medium": (3.0, 5.5),
    "high": (5.5, 99.0),
}

# Rating ranges (0-5)
RATING_RANGES = {
    "low": (0, 2.0),
    "medium": (2.0, 3.5),
    "high": (3.5, 99.0),
}

# Favourite count ranges
FAVOURITE_COUNT_RANGES = {
    "low": (0, 10),
    "medium": (10, 100),
    "high": (100, 9999999),
}

# Play count ranges
PLAY_COUNT_RANGES = {
    "low": (0, 100),
    "medium": (100, 1000),
    "high": (1000, 999999999),
}


class SearchTestFixtureFetcher(FixtureDataFetcher):
    """Coverage-gated fetcher that classifies random results into all
    applicable search test buckets simultaneously.

    One get_beatmap() call fills 10+ coverage buckets at once.
    One search_beatmapsets() call fills 20+ buckets at once.
    One get_user() call fills country/restricted coverage at once.
    """

    def __init__(self, rc: RedisClient, id_ranges: dict | None = None,
                 id_source: IDSource | None = None):
        super().__init__(rc, id_ranges, id_source=id_source)
        
        # Set default logger if not provided
        if self.logger is None:
            from app.logging import get_logger
            self.logger = get_logger(__name__)

        # Load coverage state before scanning disk (disk scan supplements coverage)
        self._load_coverage_from_metadata()

        # Difficulty and playcount ranges for categorization
        self.difficulty_ranges = {
            "easy": (0, 2.0),
            "medium": (2.0, 5.0),
            "hard": (5.0, 7.0),
            "expert": (7.0, 999.0),
        }
        self.playcount_ranges = {
            "low": (0, 100),
            "medium": (100, 1000),
            "high": (1000, 999999999),
        }

        # Set-based tracking: each key maps to a set of IDs that satisfy that bucket.
        # This allows deduplication and precise gap analysis.

        # --- Beatmapset coverage ---
        self.fetched_beatmapset_genres: dict[int, set[int]] = {}
        self.fetched_beatmapset_languages: dict[int, set[int]] = {}
        self.fetched_beatmapset_nsfw: dict[bool, set[int]] = {True: set(), False: set()}
        self.fetched_beatmapset_statuses: set[str] = set()
        self.fetched_beatmapset_titles: set[str] = set()
        self.fetched_beatmapset_artists: set[str] = set()
        self.fetched_beatmapset_creators: set[str] = set()
        self.fetched_beatmapset_sources: set[str] = set()
        self.fetched_beatmapset_tags: set[str] = set()
        self.fetched_beatmapset_ratings: dict[str, set[int]] = {"low": set(), "medium": set(), "high": set()}
        self.fetched_beatmapset_favourite_counts: dict[str, set[int]] = {"low": set(), "medium": set(), "high": set()}
        self.fetched_beatmapset_play_counts: dict[str, set[int]] = {"low": set(), "medium": set(), "high": set()}
        self.fetched_beatmapset_has_description: bool = False
        self.fetched_beatmapset_has_pack_tags: bool = False
        self.fetched_beatmapset_videos: bool = False
        self.fetched_beatmapset_storyboards: bool = False
        self.fetched_beatmapset_discussions: bool = False
        self.fetched_beatmapset_hype: bool = False
        self.fetched_beatmapset_nominations: bool = False
        self.fetched_beatmapset_sr_gaps: bool = False
        self.fetched_beatmapset_hit_lengths: bool = False

        # --- Beatmap coverage ---
        self.fetched_beatmap_modes: dict[int, set[int]] = {}
        self.fetched_beatmap_statuses: dict[str, set[int]] = {}
        self.fetched_beatmap_difficulties: dict[str, set[int]] = {"easy": set(), "medium": set(), "hard": set(), "expert": set()}
        self.fetched_beatmap_playcounts: dict[str, set[int]] = {"low": set(), "medium": set(), "high": set()}
        self.fetched_beatmap_versions: set[str] = set()
        self.fetched_beatmap_bpm: dict[str, set[int]] = {"low": set(), "medium": set(), "high": set()}
        self.fetched_beatmap_accuracy: dict[str, set[int]] = {"low": set(), "medium": set(), "high": set()}
        self.fetched_beatmap_hit_lengths: dict[str, set[int]] = {"short": set(), "medium": set(), "long": set()}
        self.fetched_beatmap_max_combos: dict[str, set[int]] = {"low": set(), "medium": set(), "high": set()}
        self.fetched_beatmap_drain: dict[str, set[int]] = {"low": set(), "medium": set(), "high": set()}
        self.fetched_beatmap_ar: dict[str, set[int]] = {"low": set(), "medium": set(), "high": set()}
        self.fetched_beatmap_cs: dict[str, set[int]] = {"low": set(), "medium": set(), "high": set()}

        # --- User coverage ---
        self.fetched_country_codes: dict[str, set[int]] = {}
        self.fetched_restricted_users: dict[bool, set[int]] = {True: set(), False: set()}

    # ------------------------------------------------------------------
    # Classification helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _categorize_range(value: float, ranges: dict[str, tuple[float, float]]) -> str | None:
        """Return the category key for a numeric value, or None if out of range.

        Uses half-open intervals: all ranges except the last are [lo, hi).
        The last range is [lo, hi] to catch edge values.
        """
        items = list(ranges.items())
        for i, (category, (lo, hi)) in enumerate(items):
            if i == len(items) - 1:
                if lo <= value <= hi:
                    return category
            else:
                if lo <= value < hi:
                    return category
        return None

    def _classify_beatmap(self, beatmap_data: dict, beatmap_id: int) -> dict[str, Any]:
        """Classify a beatmap into all applicable coverage buckets.

        Returns a dict of {bucket_name: {category: id_set}} for newly populated buckets.
        """
        classifications: dict[str, dict[str, set[int]]] = {}

        # mode
        mode_int = beatmap_data.get("mode_int")
        if mode_int is not None:
            if mode_int not in self.fetched_beatmap_modes:
                self.fetched_beatmap_modes[mode_int] = set()
            self.fetched_beatmap_modes[mode_int].add(beatmap_id)
            classifications.setdefault("fetched_beatmap_modes", {}).setdefault(mode_int, set()).add(beatmap_id)

        # status
        bm_status = beatmap_data.get("status")
        if bm_status is not None:
            status_str = str(bm_status)
            if status_str not in self.fetched_beatmap_statuses:
                self.fetched_beatmap_statuses[status_str] = set()
            self.fetched_beatmap_statuses[status_str].add(beatmap_id)
            classifications.setdefault("fetched_beatmap_statuses", {}).setdefault(status_str, set()).add(beatmap_id)

        # difficulty_rating
        diff = beatmap_data.get("difficulty_rating")
        if diff is not None:
            cat = self._categorize_range(diff, self.difficulty_ranges)
            if cat:
                self.fetched_beatmap_difficulties[cat].add(beatmap_id)
                classifications.setdefault("fetched_beatmap_difficulties", {}).setdefault(cat, set()).add(beatmap_id)

        # playcount
        pc = beatmap_data.get("playcount")
        if pc is not None:
            cat = self._categorize_range(pc, self.playcount_ranges)
            if cat:
                self.fetched_beatmap_playcounts[cat].add(beatmap_id)
                classifications.setdefault("fetched_beatmap_playcounts", {}).setdefault(cat, set()).add(beatmap_id)

        # bpm
        bpm = beatmap_data.get("bpm")
        if bpm is not None:
            cat = self._categorize_range(bpm, BPM_RANGES)
            if cat:
                self.fetched_beatmap_bpm[cat].add(beatmap_id)
                classifications.setdefault("fetched_beatmap_bpm", {}).setdefault(cat, set()).add(beatmap_id)

        # accuracy
        acc = beatmap_data.get("accuracy")
        if acc is not None:
            cat = self._categorize_range(acc, ACCURACY_RANGES)
            if cat:
                self.fetched_beatmap_accuracy[cat].add(beatmap_id)
                classifications.setdefault("fetched_beatmap_accuracy", {}).setdefault(cat, set()).add(beatmap_id)

        # hit_length
        hl = beatmap_data.get("hit_length")
        if hl is not None:
            cat = self._categorize_range(hl, HIT_LENGTH_RANGES)
            if cat:
                self.fetched_beatmap_hit_lengths[cat].add(beatmap_id)
                classifications.setdefault("fetched_beatmap_hit_lengths", {}).setdefault(cat, set()).add(beatmap_id)

        # max_combo
        mc = beatmap_data.get("max_combo")
        if mc is not None:
            cat = self._categorize_range(mc, MAX_COMBO_RANGES)
            if cat:
                self.fetched_beatmap_max_combos[cat].add(beatmap_id)
                classifications.setdefault("fetched_beatmap_max_combos", {}).setdefault(cat, set()).add(beatmap_id)

        # drain
        drain = beatmap_data.get("drain")
        if drain is not None:
            cat = self._categorize_range(drain, DRAIN_RANGES)
            if cat:
                self.fetched_beatmap_drain[cat].add(beatmap_id)
                classifications.setdefault("fetched_beatmap_drain", {}).setdefault(cat, set()).add(beatmap_id)

        # ar
        ar = beatmap_data.get("ar")
        if ar is not None:
            cat = self._categorize_range(ar, AR_RANGES)
            if cat:
                self.fetched_beatmap_ar[cat].add(beatmap_id)
                classifications.setdefault("fetched_beatmap_ar", {}).setdefault(cat, set()).add(beatmap_id)

        # cs
        cs = beatmap_data.get("cs")
        if cs is not None:
            cat = self._categorize_range(cs, CS_RANGES)
            if cat:
                self.fetched_beatmap_cs[cat].add(beatmap_id)
                classifications.setdefault("fetched_beatmap_cs", {}).setdefault(cat, set()).add(beatmap_id)

        # version (string — collect distinct)
        version = beatmap_data.get("version")
        if version:
            self.fetched_beatmap_versions.add(version)

        return classifications

    def _classify_beatmapset(self, bs_data: dict, bs_id: int) -> dict[str, Any]:
        """Classify a beatmapset into all applicable coverage buckets."""
        classifications: dict[str, Any] = {}

        # genre
        genre = bs_data.get("genre")
        if genre and isinstance(genre, dict):
            genre_id = genre.get("id")
            if genre_id is not None:
                if genre_id not in self.fetched_beatmapset_genres:
                    self.fetched_beatmapset_genres[genre_id] = set()
                self.fetched_beatmapset_genres[genre_id].add(bs_id)
                classifications.setdefault("fetched_beatmapset_genres", {}).setdefault(genre_id, set()).add(bs_id)

        # language
        lang = bs_data.get("language")
        if lang and isinstance(lang, dict):
            lang_id = lang.get("id")
            if lang_id is not None:
                if lang_id not in self.fetched_beatmapset_languages:
                    self.fetched_beatmapset_languages[lang_id] = set()
                self.fetched_beatmapset_languages[lang_id].add(bs_id)
                classifications.setdefault("fetched_beatmapset_languages", {}).setdefault(lang_id, set()).add(bs_id)

        # nsfw
        nsfw = bs_data.get("nsfw", False)
        self.fetched_beatmapset_nsfw[bool(nsfw)].add(bs_id)
        classifications.setdefault("fetched_beatmapset_nsfw", {}).setdefault(bool(nsfw), set()).add(bs_id)

        # status
        bs_status = bs_data.get("status")
        if bs_status:
            self.fetched_beatmapset_statuses.add(bs_status)
            classifications.setdefault("fetched_beatmapset_statuses", set()).add(bs_status)

        # title / artist / creator — collect distinct substrings (first 30 chars)
        title = bs_data.get("title") or bs_data.get("title_unicode") or ""
        if title:
            self.fetched_beatmapset_titles.add(title[:30])
        artist = bs_data.get("artist") or bs_data.get("artist_unicode") or ""
        if artist:
            self.fetched_beatmapset_artists.add(artist[:30])
        creator = bs_data.get("creator") or ""
        if creator:
            self.fetched_beatmapset_creators.add(creator)

        # source
        source = bs_data.get("source") or ""
        if source:
            self.fetched_beatmapset_sources.add(source)

        # tags
        tags = bs_data.get("tags") or ""
        if tags:
            for tag in str(tags).split():
                self.fetched_beatmapset_tags.add(tag)

        # rating
        rating = bs_data.get("rating")
        if rating is not None:
            cat = self._categorize_range(rating, RATING_RANGES)
            if cat:
                self.fetched_beatmapset_ratings[cat].add(bs_id)
                classifications.setdefault("fetched_beatmapset_ratings", {}).setdefault(cat, set()).add(bs_id)

        # favourite_count
        fav = bs_data.get("favourite_count")
        if fav is not None:
            cat = self._categorize_range(fav, FAVOURITE_COUNT_RANGES)
            if cat:
                self.fetched_beatmapset_favourite_counts[cat].add(bs_id)
                classifications.setdefault("fetched_beatmapset_favourite_counts", {}).setdefault(cat, set()).add(bs_id)

        # play_count
        pc = bs_data.get("play_count")
        if pc is not None:
            cat = self._categorize_range(pc, PLAY_COUNT_RANGES)
            if cat:
                self.fetched_beatmapset_play_counts[cat].add(bs_id)
                classifications.setdefault("fetched_beatmapset_play_counts", {}).setdefault(cat, set()).add(bs_id)

        # description (non-empty)
        desc = bs_data.get("description")
        if desc:
            desc_str = desc.get("description", "") if isinstance(desc, dict) else str(desc)
            if desc_str and desc_str.strip():
                self.fetched_beatmapset_has_description = True

        # pack_tags
        if bs_data.get("pack_tags"):
            self.fetched_beatmapset_has_pack_tags = True

        # video
        if bs_data.get("video"):
            self.fetched_beatmapset_videos = True

        # storyboard
        if bs_data.get("storyboard"):
            self.fetched_beatmapset_storyboards = True

        # discussion_enabled
        if bs_data.get("discussion_enabled") is not None:
            self.fetched_beatmapset_discussions = True

        # hype
        if bs_data.get("hype") is not None:
            self.fetched_beatmapset_hype = True

        # nominations
        noms = bs_data.get("current_nominations")
        if noms and isinstance(noms, dict):
            if noms.get("nominators"):
                self.fetched_beatmapset_nominations = True

        # sr_gaps / hit_lengths — track from beatmaps within the beatmapset
        beatmaps = bs_data.get("beatmaps", [])
        has_sr_gaps = False
        has_hit_lengths = False
        for bm in beatmaps:
            if bm.get("difficulty_rating") is not None:
                has_sr_gaps = True
            if bm.get("hit_length") is not None:
                has_hit_lengths = True
        if has_sr_gaps:
            self.fetched_beatmapset_sr_gaps = True
        if has_hit_lengths:
            self.fetched_beatmapset_hit_lengths = True

        return classifications

    def _classify_user(self, user_data: dict, user_id: int) -> dict[str, Any]:
        """Classify a user into all applicable coverage buckets."""
        classifications: dict[str, Any] = {}

        # country_code
        cc = user_data.get("country_code")
        if cc:
            if cc not in self.fetched_country_codes:
                self.fetched_country_codes[cc] = set()
            self.fetched_country_codes[cc].add(user_id)
            classifications.setdefault("fetched_country_codes", {}).setdefault(cc, set()).add(user_id)

        # is_restricted
        restricted = user_data.get("is_restricted", False)
        self.fetched_restricted_users[bool(restricted)].add(user_id)
        classifications.setdefault("fetched_restricted_users", {}).setdefault(bool(restricted), set()).add(user_id)

        return classifications

    # ------------------------------------------------------------------
    # Unified fetch methods
    # ------------------------------------------------------------------

    async def fetch_random_beatmaps(
        self,
        max_calls: int = 100,
        min_per_bucket: int = 1,
    ) -> dict[str, int]:
        """Fetch random beatmaps and classify each into ALL applicable buckets.

        One get_beatmap() call classifies into: mode, status, difficulty,
        playcount, bpm, accuracy, hit_length, max_combo, drain, ar, cs, version.

        Returns a dict of {bucket_name: count_of_newly_filled_buckets}.
        """
        path = get_fixture_path("beatmaps")
        newly_filled: dict[str, int] = {}
        total_calls = 0
        seen_ids: set[int] = set()

        while total_calls < max_calls:
            total_calls += 1
            beatmap_id = self._get_random_id("beatmaps", avoid_failed=True)
            if beatmap_id in seen_ids:
                continue
            seen_ids.add(beatmap_id)

            try:
                beatmap_data = await self.oac.get_beatmap(beatmap_id)
            except Exception as e:
                self.logger.debug(f"Failed to fetch beatmap {beatmap_id}: {e}")
                self._add_failed_id("beatmaps", beatmap_id)
                continue

            # Save the JSON fixture file
            filepath = path / f"beatmap_{beatmap_id}.json"
            with open(filepath, "w") as f:
                json.dump(beatmap_data, f, indent=2)

            # Classify into all buckets
            classifications = self._classify_beatmap(beatmap_data, beatmap_id)

            # Update newly_filled counters
            for bucket_name, cats in classifications.items():
                if isinstance(cats, dict):
                    for cat, ids in cats.items():
                        if len(ids) == 1:  # newly populated
                            key = f"{bucket_name}.{cat}"
                            newly_filled[key] = newly_filled.get(key, 0) + 1
                elif isinstance(cats, set):
                    if len(cats) == 1:
                        key = bucket_name
                        newly_filled[key] = newly_filled.get(key, 0) + 1

            # Update metadata counts
            self.metadata["samples"]["beatmaps"]["count"] = (
                self.metadata["samples"]["beatmaps"].get("count", 0) + 1
            )

            self.logger.debug(
                f"Fetched beatmap {beatmap_id} "
                f"(mode={beatmap_data.get('mode_int')}, "
                f"status={beatmap_data.get('status')}, "
                f"diff={beatmap_data.get('difficulty_rating')})"
            )

        self.metadata["samples"]["beatmaps"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        self._save_search_test_coverage_metadata()
        return newly_filled

    async def fetch_random_beatmapsets(
        self,
        max_calls: int = 100,
        min_per_bucket: int = 1,
    ) -> dict[str, int]:
        """Fetch random beatmapsets via search and classify into ALL buckets.

        One search_beatmapsets() call classifies into: genre, language, nsfw,
        status, title, artist, creator, source, tags, rating, favourite_count,
        play_count, description, pack_tags, video, storyboard, discussion,
        hype, nominations, sr_gaps, hit_lengths.

        Returns a dict of {bucket_name: count_of_newly_filled_buckets}.
        """
        self.logger.debug(f"fetch_random_beatmapsets starting with max_calls={max_calls}")
        path = get_fixture_path("beatmapsets")
        newly_filled: dict[str, int] = {}
        total_calls = 0
        seen_ids: set[int] = set()

        # Cycle through osu! API status filters to fill all status buckets
        # API uses numeric status values: -2=graveyard, -1=wip, 0=pending, 1=ranked, 2=approved, 3=qualified, 4=loved
        # Note: approved (2), qualified (3), and graveyard (-2) return 0 results via search
        # These are either transitional states (approved, qualified) or rare (graveyard)
        # Note: deleted beatmapsets are removed from API and don't appear in search
        search_statuses = [1, 4, 0, -1]  # ranked, loved, pending, wip
        status_index = 0

        while total_calls < max_calls:
            total_calls += 1
            page = random.randint(1, 100)
            status = search_statuses[status_index % len(search_statuses)]
            status_index += 1

            try:
                data = await self.oac.search_beatmapsets(page=page, status=status)
            except Exception as e:
                self.logger.debug(f"Error searching beatmapsets page={page} status={status}: {e}")
                continue

            beatmapsets = data.get("beatmapsets", [])
            if not beatmapsets:
                continue

            for bs_data in beatmapsets:
                # Check if we've exceeded the call budget (each get_beatmapset is 1 call)
                if total_calls >= max_calls:
                    break

                bs_id = bs_data.get("beatmapset_id") or bs_data.get("id")
                if not bs_id or bs_id in seen_ids:
                    continue
                seen_ids.add(bs_id)

                try:
                    bs_full = await self.oac.get_beatmapset(bs_id)
                    total_calls += 1  # Count the get_beatmapset call
                except Exception as e:
                    self.logger.debug(f"Failed to fetch beatmapset {bs_id}: {e}")
                    self._add_failed_id("beatmapsets", bs_id)
                    continue

                # Save the JSON fixture file
                filepath = path / f"beatmapset_{bs_id}.json"
                with open(filepath, "w") as f:
                    json.dump(bs_full, f, indent=2)

                # Classify into all buckets
                classifications = self._classify_beatmapset(bs_full, bs_id)

                # Update newly_filled counters
                for bucket_name, cats in classifications.items():
                    if isinstance(cats, dict):
                        for cat, ids in cats.items():
                            if len(ids) == 1:
                                key = f"{bucket_name}.{cat}"
                                newly_filled[key] = newly_filled.get(key, 0) + 1
                    elif isinstance(cats, set):
                        if len(cats) == 1:
                            newly_filled[bucket_name] = newly_filled.get(bucket_name, 0) + 1
                    elif isinstance(cats, bool):
                        if cats:
                            newly_filled[bucket_name] = newly_filled.get(bucket_name, 0) + 1

                self.metadata["samples"]["beatmapsets"]["count"] = (
                    self.metadata["samples"]["beatmapsets"].get("count", 0) + 1
                )

                # Log all classified buckets for this beatmapset (abbreviated)
                bucket_aliases = {
                    "fetched_beatmapset_genres": "genre",
                    "fetched_beatmapset_languages": "lang",
                    "fetched_beatmapset_nsfw": "nsfw",
                    "fetched_beatmapset_statuses": "status",
                    "fetched_beatmapset_ratings": "rating",
                    "fetched_beatmapset_favourite_counts": "fav",
                    "fetched_beatmapset_play_counts": "plays",
                    "fetched_beatmapset_has_description": "desc",
                    "fetched_beatmapset_has_pack_tags": "pack",
                    "fetched_beatmapset_videos": "video",
                    "fetched_beatmapset_storyboards": "storyboard",
                    "fetched_beatmapset_discussions": "disc",
                    "fetched_beatmapset_hype": "hype",
                    "fetched_beatmapset_nominations": "noms",
                    "fetched_beatmapset_sr_gaps": "sr_gaps",
                    "fetched_beatmapset_hit_lengths": "hit_len",
                    "fetched_beatmap_modes": "mode",
                    "fetched_beatmap_statuses": "bm_status",
                    "fetched_beatmap_difficulties": "diff",
                    "fetched_beatmap_playcounts": "bm_plays",
                    "fetched_beatmap_bpm": "bpm",
                    "fetched_beatmap_accuracy": "acc",
                    "fetched_beatmap_hit_lengths": "bm_hit_len",
                    "fetched_beatmap_max_combos": "max_combo",
                    "fetched_beatmap_drain": "drain",
                    "fetched_beatmap_ar": "ar",
                    "fetched_beatmap_cs": "cs",
                    "fetched_country_codes": "country",
                    "fetched_restricted_users": "restricted",
                }
                log_parts = [f"bs {bs_id}"]
                for bucket_name, cats in classifications.items():
                    alias = bucket_aliases.get(bucket_name, bucket_name.split("_")[-1])
                    if isinstance(cats, dict):
                        for cat, ids in cats.items():
                            if len(ids) == 1:
                                log_parts.append(f"{alias}:{cat}")
                    elif isinstance(cats, set) and len(cats) == 1:
                        log_parts.append(f"{alias}:{next(iter(cats))}")
                    elif isinstance(cats, bool) and cats:
                        log_parts.append(alias)
                self.logger.debug(f"Fetched {', '.join(log_parts)}")

        self.metadata["samples"]["beatmapsets"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        self._save_search_test_coverage_metadata()
        return newly_filled

    async def fetch_random_users(
        self,
        max_calls: int = 100,
        min_per_bucket: int = 1,
    ) -> dict[str, int]:
        """Fetch random users via rankings and classify into all buckets.

        One get_user() call fills: country_code, is_restricted.
        Cycles through all rulesets (osu, taiko, fruits, mania) for diverse country codes.

        Returns a dict of {bucket_name: count_of_newly_filled_buckets}.
        """
        from .utils import RULESETS
        from app.osu_api.enums import Ruleset as RulesetEnum

        path = get_fixture_path("users")
        newly_filled: dict[str, int] = {}
        total_calls = 0
        seen_ids: set[int] = set()
        page = 1
        ruleset_index = 0
        rulesets = [RulesetEnum.OSU, RulesetEnum.TAIKO, RulesetEnum.FRUITS, RulesetEnum.MANIA]

        while total_calls < max_calls:
            ruleset = rulesets[ruleset_index % len(rulesets)]
            ruleset_name = ruleset.name.lower()

            try:
                data = await self.oac.get_rankings(
                    ruleset=ruleset,
                    mode="performance",
                    cursor_page=page,
                    limit=50,
                )
            except Exception as e:
                self.logger.debug(f"Error fetching rankings page={page} for {ruleset_name}: {e}")
                break

            players = data.get("ranking", [])
            if not players:
                ruleset_index += 1
                page = 1
                continue

            for player in players:
                if total_calls >= max_calls:
                    break
                user = player.get("user")
                if not user:
                    continue
                user_id = user.get("id")
                if not user_id or user_id in seen_ids:
                    continue

                total_calls += 1
                seen_ids.add(user_id)

                try:
                    user_data = await self.oac.get_user(user_id, ruleset)
                except Exception as e:
                    self.logger.debug(f"Failed to fetch user {user_id}: {e}")
                    self._add_failed_id(f"users.{ruleset_name}", user_id)
                    continue

                # Save the JSON fixture file
                ruleset_path = path / ruleset_name
                ruleset_path.mkdir(parents=True, exist_ok=True)
                filepath = ruleset_path / f"user_{user_id}_{ruleset_name}.json"
                self._atomic_write(filepath, user_data, "user")

                # Classify into all buckets
                classifications = self._classify_user(user_data, user_id)

                # Update newly_filled counters
                for bucket_name, cats in classifications.items():
                    if isinstance(cats, dict):
                        for cat, ids in cats.items():
                            if len(ids) == 1:
                                key = f"{bucket_name}.{cat}"
                                newly_filled[key] = newly_filled.get(key, 0) + 1

                self.metadata["samples"]["users"]["count"] = (
                    self.metadata["samples"]["users"].get("count", 0) + 1
                )
                self.metadata["samples"]["users"]["per_ruleset"][ruleset_name] = (
                    self.metadata["samples"]["users"]["per_ruleset"].get(ruleset_name, 0) + 1
                )

                self.logger.debug(
                    f"Fetched user {user_id} ({ruleset_name}) "
                    f"(country={user_data.get('country_code')}, "
                    f"restricted={user_data.get('is_restricted')})"
                )

            page += 1
            if len(players) < 50:
                ruleset_index += 1
                page = 1
            else:
                ruleset_index += 1

        self.metadata["samples"]["users"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        self._save_search_test_coverage_metadata()
        return newly_filled

    async def fetch_special_beatmapsets(
        self,
        max_calls: int = 50,
    ) -> dict[str, int]:
        """Fetch beatmapsets with hard-to-find properties (NSFW, graveyard status, restricted users).

        These are not reliably found via search API, so we fetch by known IDs
        or random ID probing.

        Returns a dict of {bucket_name: count_of_newly_filled_buckets}.
        """
        self.logger.debug(f"fetch_special_beatmapsets starting with max_calls={max_calls}")
        path = get_fixture_path("beatmapsets")
        newly_filled: dict[str, int] = {}
        total_calls = 0
        seen_ids: set[int] = set()

        # Start with known IDs (restricted, NSFW, graveyard)
        candidate_ids = list(RESTRICTED_BEATMAPSET_IDS) + list(NSFW_BEATMAPSET_IDS)

        # Add random IDs for probing
        while len(candidate_ids) < max_calls * 2:
            candidate_ids.append(random.randint(1, 20000000))

        random.shuffle(candidate_ids)

        for bs_id in candidate_ids:
            if total_calls >= max_calls:
                break
            if bs_id in seen_ids:
                continue
            seen_ids.add(bs_id)

            try:
                bs_full = await self.oac.get_beatmapset(bs_id)
                total_calls += 1
            except Exception as e:
                self.logger.debug(f"Failed to fetch beatmapset {bs_id}: {e}")
                self._add_failed_id("beatmapsets", bs_id)
                continue

            # Save the JSON fixture file
            filepath = path / f"beatmapset_{bs_id}.json"
            with open(filepath, "w") as f:
                json.dump(bs_full, f, indent=2)

            # Check for restricted user (deleted or inactive user)
            user = bs_full.get("user") or {}
            if user.get("is_deleted") or (not user.get("is_active") and user.get("id")):
                # This beatmapset has a restricted or deleted user
                self.fetched_restricted_users[True].add(bs_id)
                newly_filled["fetched_restricted_users.True"] = newly_filled.get("fetched_restricted_users.True", 0) + 1
                self.logger.debug(f"Found restricted user reference in bs {bs_id} (deleted={user.get('is_deleted')}, active={user.get('is_active')})")

            # Classify into all buckets
            classifications = self._classify_beatmapset(bs_full, bs_id)

            # Update newly_filled counters
            for bucket_name, cats in classifications.items():
                if isinstance(cats, dict):
                    for cat, ids in cats.items():
                        if len(ids) == 1:
                            key = f"{bucket_name}.{cat}"
                            newly_filled[key] = newly_filled.get(key, 0) + 1
                elif isinstance(cats, set):
                    if len(cats) == 1:
                        newly_filled[bucket_name] = newly_filled.get(bucket_name, 0) + 1
                elif isinstance(cats, bool):
                    if cats:
                        newly_filled[bucket_name] = newly_filled.get(bucket_name, 0) + 1

            self.metadata["samples"]["beatmapsets"]["count"] = (
                self.metadata["samples"]["beatmapsets"].get("count", 0) + 1
            )

            self.logger.debug(
                f"Fetched special bs {bs_id} "
                f"(nsfw={bs_full.get('nsfw')}, "
                f"status={bs_full.get('status')}, "
                f"restricted_user={not bool(bs_full.get('user'))})"
            )

        self.metadata["samples"]["beatmapsets"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        self._save_search_test_coverage_metadata()
        return newly_filled

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------

    def _get_bucket_coverage_status(self) -> dict[str, dict]:
        """Return the current coverage status for every bucket.

        Returns dict of {bucket_name: {category: bool (has_min_coverage)}}.
        """
        status: dict[str, dict] = {}

        # Beatmapset buckets
        for genre_id, ids in self.fetched_beatmapset_genres.items():
            status.setdefault("fetched_beatmapset_genres", {})[genre_id] = len(ids) >= 1
        for lang_id, ids in self.fetched_beatmapset_languages.items():
            status.setdefault("fetched_beatmapset_languages", {})[lang_id] = len(ids) >= 1
        status["fetched_beatmapset_nsfw"] = {
            True: len(self.fetched_beatmapset_nsfw[True]) >= 1,
            False: len(self.fetched_beatmapset_nsfw[False]) >= 1,
        }
        status["fetched_beatmapset_statuses"] = {s: s in self.fetched_beatmapset_statuses for s in self.fetched_beatmapset_statuses}
        status["fetched_beatmapset_has_description"] = {"covered": self.fetched_beatmapset_has_description}
        status["fetched_beatmapset_has_pack_tags"] = {"covered": self.fetched_beatmapset_has_pack_tags}
        status["fetched_beatmapset_videos"] = {"covered": self.fetched_beatmapset_videos}
        status["fetched_beatmapset_storyboards"] = {"covered": self.fetched_beatmapset_storyboards}
        status["fetched_beatmapset_discussions"] = {"covered": self.fetched_beatmapset_discussions}
        status["fetched_beatmapset_hype"] = {"covered": self.fetched_beatmapset_hype}
        status["fetched_beatmapset_nominations"] = {"covered": self.fetched_beatmapset_nominations}
        status["fetched_beatmapset_sr_gaps"] = {"covered": self.fetched_beatmapset_sr_gaps}
        status["fetched_beatmapset_hit_lengths"] = {"covered": self.fetched_beatmapset_hit_lengths}

        # Rating / fav / play count buckets
        for cat in ("low", "medium", "high"):
            status.setdefault("fetched_beatmapset_ratings", {})[cat] = len(self.fetched_beatmapset_ratings[cat]) >= 1
            status.setdefault("fetched_beatmapset_favourite_counts", {})[cat] = len(self.fetched_beatmapset_favourite_counts[cat]) >= 1
            status.setdefault("fetched_beatmapset_play_counts", {})[cat] = len(self.fetched_beatmapset_play_counts[cat]) >= 1

        # Beatmap buckets
        for mode_int, ids in self.fetched_beatmap_modes.items():
            status.setdefault("fetched_beatmap_modes", {})[mode_int] = len(ids) >= 1
        for status_str, ids in self.fetched_beatmap_statuses.items():
            status.setdefault("fetched_beatmap_statuses", {})[status_str] = len(ids) >= 1
        for cat in ("easy", "medium", "hard", "expert"):
            status.setdefault("fetched_beatmap_difficulties", {})[cat] = len(self.fetched_beatmap_difficulties[cat]) >= 1
        for cat in ("low", "medium", "high"):
            status.setdefault("fetched_beatmap_playcounts", {})[cat] = len(self.fetched_beatmap_playcounts[cat]) >= 1
        status["fetched_beatmap_versions"] = {"covered": len(self.fetched_beatmap_versions) >= 1}
        for cat in ("low", "medium", "high"):
            status.setdefault("fetched_beatmap_bpm", {})[cat] = len(self.fetched_beatmap_bpm[cat]) >= 1
            status.setdefault("fetched_beatmap_accuracy", {})[cat] = len(self.fetched_beatmap_accuracy[cat]) >= 1
            status.setdefault("fetched_beatmap_max_combos", {})[cat] = len(self.fetched_beatmap_max_combos[cat]) >= 1
            status.setdefault("fetched_beatmap_drain", {})[cat] = len(self.fetched_beatmap_drain[cat]) >= 1
            status.setdefault("fetched_beatmap_ar", {})[cat] = len(self.fetched_beatmap_ar[cat]) >= 1
            status.setdefault("fetched_beatmap_cs", {})[cat] = len(self.fetched_beatmap_cs[cat]) >= 1
        for cat in ("short", "medium", "long"):
            status.setdefault("fetched_beatmap_hit_lengths", {})[cat] = len(self.fetched_beatmap_hit_lengths[cat]) >= 1

        # User buckets
        for cc, ids in self.fetched_country_codes.items():
            status.setdefault("fetched_country_codes", {})[cc] = len(ids) >= 1
        status["fetched_restricted_users"] = {
            True: len(self.fetched_restricted_users[True]) >= 1,
            False: len(self.fetched_restricted_users[False]) >= 1,
        }

        return status

    def _count_uncovered_buckets(self, status: dict[str, dict]) -> int:
        """Count total number of uncovered bucket entries."""
        count = 0
        for bucket, cats in status.items():
            if isinstance(cats, dict):
                for cat, covered in cats.items():
                    if not covered:
                        count += 1
        return count

    def _load_coverage_from_metadata(self) -> None:
        """Load previously persisted search test coverage from metadata.json."""
        search_cov = self.metadata.get("search_test_coverage", {})
        if not search_cov:
            return

        # Load beatmapset genres
        for genre_id in search_cov.get("beatmapset_genres", []):
            self.fetched_beatmapset_genres.setdefault(genre_id, set())

        # Load beatmapset languages
        for lang_id in search_cov.get("beatmapset_languages", []):
            self.fetched_beatmapset_languages.setdefault(lang_id, set())

        # Load NSFW
        for bs_id in search_cov.get("beatmapset_nsfw_true_ids", []):
            self.fetched_beatmapset_nsfw[True].add(bs_id)
        for bs_id in search_cov.get("beatmapset_nsfw_false_ids", []):
            self.fetched_beatmapset_nsfw[False].add(bs_id)

        # Load statuses
        for s in search_cov.get("beatmapset_statuses", []):
            self.fetched_beatmapset_statuses.add(s)

        # Load titles/artists/creators/sources/tags (just presence, not IDs)
        for t in search_cov.get("beatmapset_titles", []):
            self.fetched_beatmapset_titles.add(t)
        for a in search_cov.get("beatmapset_artists", []):
            self.fetched_beatmapset_artists.add(a)
        for c in search_cov.get("beatmapset_creators", []):
            self.fetched_beatmapset_creators.add(c)
        for s in search_cov.get("beatmapset_sources", []):
            self.fetched_beatmapset_sources.add(s)
        for t in search_cov.get("beatmapset_tags", []):
            self.fetched_beatmapset_tags.add(t)

        # Load beatmap modes
        for m in search_cov.get("beatmap_modes", []):
            self.fetched_beatmap_modes.setdefault(m, set())

        # Load beatmap statuses
        for s in search_cov.get("beatmap_statuses", []):
            self.fetched_beatmap_statuses.setdefault(s, set())

        # Load difficulties
        for cat, ids in search_cov.get("beatmap_difficulties", {}).items():
            if cat in self.fetched_beatmap_difficulties:
                self.fetched_beatmap_difficulties[cat].update(ids)

        # Load playcounts
        for cat, ids in search_cov.get("beatmap_playcounts", {}).items():
            if cat in self.fetched_beatmap_playcounts:
                self.fetched_beatmap_playcounts[cat].update(ids)

        # Load versions
        for v in search_cov.get("beatmap_versions", []):
            self.fetched_beatmap_versions.add(v)

        # Load country codes
        for cc in search_cov.get("country_codes", []):
            self.fetched_country_codes.setdefault(cc, set())

        # Load restricted users
        for uid in search_cov.get("restricted_users", {}).get("true_ids", []):
            self.fetched_restricted_users[True].add(uid)
        for uid in search_cov.get("restricted_users", {}).get("false_ids", []):
            self.fetched_restricted_users[False].add(uid)

    def _save_search_test_coverage_metadata(self) -> None:
        """Persist current coverage state to metadata.json."""
        MAX_COVERAGE_LIST_SIZE = 200
        self.metadata["search_test_coverage"] = {
            "beatmapset_genres": sorted(self.fetched_beatmapset_genres.keys())[:MAX_COVERAGE_LIST_SIZE],
            "beatmapset_languages": sorted(self.fetched_beatmapset_languages.keys())[:MAX_COVERAGE_LIST_SIZE],
            "beatmapset_nsfw_true_ids": sorted(self.fetched_beatmapset_nsfw[True])[:MAX_COVERAGE_LIST_SIZE],
            "beatmapset_nsfw_false_ids": sorted(self.fetched_beatmapset_nsfw[False])[:MAX_COVERAGE_LIST_SIZE],
            "beatmapset_statuses": sorted(self.fetched_beatmapset_statuses)[:MAX_COVERAGE_LIST_SIZE],
            "beatmapset_titles": sorted(self.fetched_beatmapset_titles)[:MAX_COVERAGE_LIST_SIZE],
            "beatmapset_artists": sorted(self.fetched_beatmapset_artists)[:MAX_COVERAGE_LIST_SIZE],
            "beatmapset_creators": sorted(self.fetched_beatmapset_creators)[:MAX_COVERAGE_LIST_SIZE],
            "beatmapset_sources": sorted(self.fetched_beatmapset_sources)[:MAX_COVERAGE_LIST_SIZE],
            "beatmapset_tags": sorted(self.fetched_beatmapset_tags)[:MAX_COVERAGE_LIST_SIZE],
            "beatmap_modes": sorted(self.fetched_beatmap_modes.keys())[:MAX_COVERAGE_LIST_SIZE],
            "beatmap_statuses": sorted(self.fetched_beatmap_statuses.keys())[:MAX_COVERAGE_LIST_SIZE],
            "beatmap_difficulties": {
                k: sorted(v)[:MAX_COVERAGE_LIST_SIZE] for k, v in self.fetched_beatmap_difficulties.items()
            },
            "beatmap_playcounts": {
                k: sorted(v)[:MAX_COVERAGE_LIST_SIZE] for k, v in self.fetched_beatmap_playcounts.items()
            },
            "beatmap_versions": sorted(self.fetched_beatmap_versions)[:MAX_COVERAGE_LIST_SIZE],
            "country_codes": sorted(self.fetched_country_codes.keys())[:MAX_COVERAGE_LIST_SIZE],
            "restricted_users": {
                "true_ids": sorted(self.fetched_restricted_users[True])[:MAX_COVERAGE_LIST_SIZE],
                "false_ids": sorted(self.fetched_restricted_users[False])[:MAX_COVERAGE_LIST_SIZE],
            },
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        save_metadata(self.metadata)

    async def ensure_search_test_coverage(
        self,
        min_per_category: int = 1,
        max_total: int = 500,
        skip_covered: bool = False,
    ) -> dict:
        """Ensure all search test coverage buckets are populated.

        Uses an adaptive priority-based fetch loop that minimizes API calls
        by always fetching the action with the highest expected information
        gain. Stops as soon as all buckets meet min_per_category.

        Args:
            min_per_category: Minimum items per coverage bucket.
            max_total: Maximum total API calls before stopping.
            skip_covered: If True, skip buckets already at min_per_category.

        Returns:
            Coverage report dict.
        """
        self._load_coverage_from_metadata()

        if skip_covered:
            from .search_coverage import CoverageTracker
            tracker = CoverageTracker(self, min_per_category=min_per_category)
            if tracker.all_covered():
                self.logger.info("All buckets already covered. Nothing to fetch.")
                return self.get_coverage_report()

        from .search_coverage import adaptive_fetch_loop
        return await adaptive_fetch_loop(
            self,
            min_per_category=min_per_category,
            max_total=max_total,
        )

    # ------------------------------------------------------------------
    # Coverage report
    # ------------------------------------------------------------------

    def get_coverage_report(self) -> dict:
        """Get current search test coverage status."""
        return {
            "beatmapset_genres": {
                gid: {
                    "name": GENRE_NAMES.get(gid, "Unknown"),
                    "count": len(ids),
                    "ids": sorted(ids),
                }
                for gid, ids in self.fetched_beatmapset_genres.items()
            },
            "beatmapset_languages": {
                lid: {
                    "name": LANGUAGE_NAMES.get(lid, "Unknown"),
                    "count": len(ids),
                    "ids": sorted(ids),
                }
                for lid, ids in self.fetched_beatmapset_languages.items()
            },
            "beatmapset_nsfw": {
                "true": {"count": len(self.fetched_beatmapset_nsfw[True]), "ids": sorted(self.fetched_beatmapset_nsfw[True])},
                "false": {"count": len(self.fetched_beatmapset_nsfw[False]), "ids": sorted(self.fetched_beatmapset_nsfw[False])},
            },
            "beatmapset_statuses": sorted(self.fetched_beatmapset_statuses),
            "beatmapset_titles": sorted(self.fetched_beatmapset_titles)[:20],
            "beatmapset_artists": sorted(self.fetched_beatmapset_artists)[:20],
            "beatmapset_creators": sorted(self.fetched_beatmapset_creators)[:20],
            "beatmapset_sources": sorted(self.fetched_beatmapset_sources)[:20],
            "beatmapset_tags": sorted(self.fetched_beatmapset_tags)[:20],
            "beatmapset_ratings": {
                cat: {"count": len(ids), "ids": sorted(ids)}
                for cat, ids in self.fetched_beatmapset_ratings.items()
            },
            "beatmapset_favourite_counts": {
                cat: {"count": len(ids), "ids": sorted(ids)}
                for cat, ids in self.fetched_beatmapset_favourite_counts.items()
            },
            "beatmapset_play_counts": {
                cat: {"count": len(ids), "ids": sorted(ids)}
                for cat, ids in self.fetched_beatmapset_play_counts.items()
            },
            "beatmapset_has_description": self.fetched_beatmapset_has_description,
            "beatmapset_has_pack_tags": self.fetched_beatmapset_has_pack_tags,
            "beatmapset_videos": self.fetched_beatmapset_videos,
            "beatmapset_storyboards": self.fetched_beatmapset_storyboards,
            "beatmapset_discussions": self.fetched_beatmapset_discussions,
            "beatmapset_hype": self.fetched_beatmapset_hype,
            "beatmapset_nominations": self.fetched_beatmapset_nominations,
            "beatmapset_sr_gaps": self.fetched_beatmapset_sr_gaps,
            "beatmapset_hit_lengths": self.fetched_beatmapset_hit_lengths,
            "beatmap_modes": {
                m: {"name": BEATMAP_MODE_NAMES.get(m, "Unknown"), "count": len(ids), "ids": sorted(ids)}
                for m, ids in self.fetched_beatmap_modes.items()
            },
            "beatmap_statuses": {
                s: {"name": BEATMAP_STATUS_NAMES.get(s, s), "count": len(ids), "ids": sorted(ids)}
                for s, ids in self.fetched_beatmap_statuses.items()
            },
            "beatmap_difficulties": {
                cat: {"count": len(ids), "ids": sorted(ids)}
                for cat, ids in self.fetched_beatmap_difficulties.items()
            },
            "beatmap_playcounts": {
                cat: {"count": len(ids), "ids": sorted(ids)}
                for cat, ids in self.fetched_beatmap_playcounts.items()
            },
            "beatmap_versions": sorted(self.fetched_beatmap_versions)[:20],
            "beatmap_bpm": {
                cat: {"count": len(ids), "ids": sorted(ids)}
                for cat, ids in self.fetched_beatmap_bpm.items()
            },
            "beatmap_accuracy": {
                cat: {"count": len(ids), "ids": sorted(ids)}
                for cat, ids in self.fetched_beatmap_accuracy.items()
            },
            "beatmap_hit_lengths": {
                cat: {"count": len(ids), "ids": sorted(ids)}
                for cat, ids in self.fetched_beatmap_hit_lengths.items()
            },
            "beatmap_max_combos": {
                cat: {"count": len(ids), "ids": sorted(ids)}
                for cat, ids in self.fetched_beatmap_max_combos.items()
            },
            "beatmap_drain": {
                cat: {"count": len(ids), "ids": sorted(ids)}
                for cat, ids in self.fetched_beatmap_drain.items()
            },
            "beatmap_ar": {
                cat: {"count": len(ids), "ids": sorted(ids)}
                for cat, ids in self.fetched_beatmap_ar.items()
            },
            "beatmap_cs": {
                cat: {"count": len(ids), "ids": sorted(ids)}
                for cat, ids in self.fetched_beatmap_cs.items()
            },
            "country_codes": {
                cc: {"count": len(ids), "ids": sorted(ids)}
                for cc, ids in self.fetched_country_codes.items()
            },
            "restricted_users": {
                "true": {"count": len(self.fetched_restricted_users[True]), "ids": sorted(self.fetched_restricted_users[True])},
                "false": {"count": len(self.fetched_restricted_users[False]), "ids": sorted(self.fetched_restricted_users[False])},
            },
        }
