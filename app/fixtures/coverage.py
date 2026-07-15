"""Coverage tracking registry for search test fixtures.

Replaces 50+ instance attributes in SearchTestFixtureFetcher with a data-driven
registry that tracks coverage buckets. Adding a new bucket requires registering
one entry instead of adding 3+ attributes and updating 5+ methods.
"""

from dataclasses import dataclass, field
from typing import Any, Callable
from enum import Enum


class BucketType(Enum):
    """Type of coverage bucket data structure."""
    SET = "set"
    DICT = "dict"
    BOOL = "bool"


@dataclass
class Bucket:
    """Definition of a coverage bucket.

    Attributes:
        name: Unique bucket name (e.g., "fetched_beatmapset_genres")
        bucket_type: Type of data structure (SET, DICT, BOOL)
        categorize: Optional function to map data -> bucket key (for DICT type)
        rarity_weight: How hard this bucket is to fill (higher = rarer)
        min_coverage: Minimum items required to consider covered
    """
    name: str
    bucket_type: BucketType
    categorize: Callable | None = None
    rarity_weight: float = 1.0
    min_coverage: int = 1


class CoverageRegistry:
    """Registry for tracking coverage of search test buckets.

    Provides a unified interface for classifying data into buckets,
    checking coverage status, and generating coverage reports.

    Example:
        registry = CoverageRegistry()
        registry.register(Bucket("fetched_beatmapset_genres", BucketType.DICT))
        registry.classify({"genre": {"id": 1}}, "beatmapset", 12345)
        registry.is_covered("fetched_beatmapset_genres", 1)  # True
    """

    def __init__(self):
        self._buckets: dict[str, Bucket] = {}
        self._data: dict[str, Any] = {}
        self._initialize_default_buckets()

    def _initialize_default_buckets(self) -> None:
        """Initialize with default search test buckets."""
        # Beatmapset buckets
        self.register(Bucket("fetched_beatmapset_genres", BucketType.DICT, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmapset_languages", BucketType.DICT, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmapset_nsfw", BucketType.DICT, rarity_weight=2.5))
        self.register(Bucket("fetched_beatmapset_statuses", BucketType.SET, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmapset_titles", BucketType.SET, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmapset_artists", BucketType.SET, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmapset_creators", BucketType.SET, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmapset_sources", BucketType.SET, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmapset_tags", BucketType.SET, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmapset_ratings", BucketType.DICT, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmapset_favourite_counts", BucketType.DICT, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmapset_play_counts", BucketType.DICT, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmapset_has_description", BucketType.BOOL, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmapset_has_pack_tags", BucketType.BOOL, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmapset_videos", BucketType.BOOL, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmapset_storyboards", BucketType.BOOL, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmapset_discussions", BucketType.BOOL, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmapset_hype", BucketType.BOOL, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmapset_nominations", BucketType.BOOL, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmapset_sr_gaps", BucketType.BOOL, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmapset_hit_lengths", BucketType.BOOL, rarity_weight=1.0))

        # Beatmap buckets
        self.register(Bucket("fetched_beatmap_modes", BucketType.DICT, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmap_statuses", BucketType.DICT, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmap_difficulties", BucketType.DICT, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmap_playcounts", BucketType.DICT, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmap_versions", BucketType.SET, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmap_bpm", BucketType.DICT, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmap_accuracy", BucketType.DICT, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmap_hit_lengths", BucketType.DICT, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmap_max_combos", BucketType.DICT, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmap_drain", BucketType.DICT, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmap_ar", BucketType.DICT, rarity_weight=1.0))
        self.register(Bucket("fetched_beatmap_cs", BucketType.DICT, rarity_weight=1.0))

        # User buckets
        self.register(Bucket("fetched_country_codes", BucketType.DICT, rarity_weight=1.0))
        self.register(Bucket("fetched_restricted_users", BucketType.DICT, rarity_weight=3.0))

        # Initialize data structures
        for bucket in self._buckets.values():
            if bucket.bucket_type == BucketType.SET:
                self._data[bucket.name] = set()
            elif bucket.bucket_type == BucketType.DICT:
                self._data[bucket.name] = {}
            elif bucket.bucket_type == BucketType.BOOL:
                self._data[bucket.name] = False

    def register(self, bucket: Bucket) -> None:
        """Register a new coverage bucket.

        Args:
            bucket: Bucket definition
        """
        self._buckets[bucket.name] = bucket
        if bucket.name not in self._data:
            if bucket.bucket_type == BucketType.SET:
                self._data[bucket.name] = set()
            elif bucket.bucket_type == BucketType.DICT:
                self._data[bucket.name] = {}
            elif bucket.bucket_type == BucketType.BOOL:
                self._data[bucket.name] = False

    def classify(self, data: dict, data_type: str, item_id: int) -> dict[str, set[int]]:
        """Classify data into coverage buckets.

        Args:
            data: Raw API response data
            data_type: Type of data ("beatmap", "beatmapset", "user")
            item_id: ID of the item being classified

        Returns:
            Dictionary of {bucket_name: set_of_new_ids} for newly populated buckets
        """
        newly_filled: dict[str, set[int]] = {}

        # Route to appropriate classifier based on data type
        if data_type == "beatmap":
            self._classify_beatmap(data, item_id, newly_filled)
        elif data_type == "beatmapset":
            self._classify_beatmapset(data, item_id, newly_filled)
        elif data_type == "user":
            self._classify_user(data, item_id, newly_filled)

        return newly_filled

    def _classify_beatmap(self, data: dict, item_id: int, newly_filled: dict[str, set[int]]) -> None:
        """Classify beatmap data into buckets."""
        # mode
        mode_int = data.get("mode_int")
        if mode_int is not None:
            self._add_to_dict_bucket("fetched_beatmap_modes", mode_int, item_id, newly_filled)

        # status
        bm_status = data.get("status")
        if bm_status is not None:
            self._add_to_dict_bucket("fetched_beatmap_statuses", str(bm_status), item_id, newly_filled)

        # difficulty_rating
        diff = data.get("difficulty_rating")
        if diff is not None:
            from .categorization import DIFFICULTY_CATEGORIZER
            cat = DIFFICULTY_CATEGORIZER.categorize(diff)
            if cat:
                self._add_to_dict_bucket("fetched_beatmap_difficulties", cat, item_id, newly_filled)

        # playcount
        pc = data.get("playcount")
        if pc is not None:
            from .categorization import PLAYCOUNT_CATEGORIZER
            cat = PLAYCOUNT_CATEGORIZER.categorize(pc)
            if cat:
                self._add_to_dict_bucket("fetched_beatmap_playcounts", cat, item_id, newly_filled)

        # bpm
        bpm = data.get("bpm")
        if bpm is not None:
            from .categorization import BPM_CATEGORIZER
            cat = BPM_CATEGORIZER.categorize(bpm)
            if cat:
                self._add_to_dict_bucket("fetched_beatmap_bpm", cat, item_id, newly_filled)

        # accuracy
        acc = data.get("accuracy")
        if acc is not None:
            from .categorization import ACCURACY_CATEGORIZER
            cat = ACCURACY_CATEGORIZER.categorize(acc)
            if cat:
                self._add_to_dict_bucket("fetched_beatmap_accuracy", cat, item_id, newly_filled)

        # hit_length
        hl = data.get("hit_length")
        if hl is not None:
            from .categorization import HIT_LENGTH_CATEGORIZER
            cat = HIT_LENGTH_CATEGORIZER.categorize(hl)
            if cat:
                self._add_to_dict_bucket("fetched_beatmap_hit_lengths", cat, item_id, newly_filled)

        # max_combo
        mc = data.get("max_combo")
        if mc is not None:
            from .categorization import MAX_COMBO_CATEGORIZER
            cat = MAX_COMBO_CATEGORIZER.categorize(mc)
            if cat:
                self._add_to_dict_bucket("fetched_beatmap_max_combos", cat, item_id, newly_filled)

        # drain
        drain = data.get("drain")
        if drain is not None:
            from .categorization import DRAIN_CATEGORIZER
            cat = DRAIN_CATEGORIZER.categorize(drain)
            if cat:
                self._add_to_dict_bucket("fetched_beatmap_drain", cat, item_id, newly_filled)

        # ar
        ar = data.get("ar")
        if ar is not None:
            from .categorization import AR_CATEGORIZER
            cat = AR_CATEGORIZER.categorize(ar)
            if cat:
                self._add_to_dict_bucket("fetched_beatmap_ar", cat, item_id, newly_filled)

        # cs
        cs = data.get("cs")
        if cs is not None:
            from .categorization import CS_CATEGORIZER
            cat = CS_CATEGORIZER.categorize(cs)
            if cat:
                self._add_to_dict_bucket("fetched_beatmap_cs", cat, item_id, newly_filled)

        # version
        version = data.get("version")
        if version:
            self._add_to_set_bucket("fetched_beatmap_versions", version, item_id, newly_filled)

    def _classify_beatmapset(self, data: dict, item_id: int, newly_filled: dict[str, set[int]]) -> None:
        """Classify beatmapset data into buckets."""
        # genre
        genre = data.get("genre")
        if genre and isinstance(genre, dict):
            genre_id = genre.get("id")
            if genre_id is not None:
                self._add_to_dict_bucket("fetched_beatmapset_genres", genre_id, item_id, newly_filled)

        # language
        lang = data.get("language")
        if lang and isinstance(lang, dict):
            lang_id = lang.get("id")
            if lang_id is not None:
                self._add_to_dict_bucket("fetched_beatmapset_languages", lang_id, item_id, newly_filled)

        # nsfw
        nsfw = data.get("nsfw", False)
        self._add_to_dict_bucket("fetched_beatmapset_nsfw", bool(nsfw), item_id, newly_filled)

        # status
        bs_status = data.get("status")
        if bs_status:
            self._add_to_set_bucket("fetched_beatmapset_statuses", str(bs_status), item_id, newly_filled)

        # title
        title = data.get("title") or data.get("title_unicode") or ""
        if title:
            self._add_to_set_bucket("fetched_beatmapset_titles", title[:30], item_id, newly_filled)

        # artist
        artist = data.get("artist") or data.get("artist_unicode") or ""
        if artist:
            self._add_to_set_bucket("fetched_beatmapset_artists", artist[:30], item_id, newly_filled)

        # creator
        creator = data.get("creator") or ""
        if creator:
            self._add_to_set_bucket("fetched_beatmapset_creators", creator, item_id, newly_filled)

        # source
        source = data.get("source") or ""
        if source:
            self._add_to_set_bucket("fetched_beatmapset_sources", source, item_id, newly_filled)

        # tags
        tags = data.get("tags") or ""
        if tags:
            for tag in str(tags).split():
                self._add_to_set_bucket("fetched_beatmapset_tags", tag, item_id, newly_filled)

        # rating
        rating = data.get("rating")
        if rating is not None:
            from .categorization import RATING_CATEGORIZER
            cat = RATING_CATEGORIZER.categorize(rating)
            if cat:
                self._add_to_dict_bucket("fetched_beatmapset_ratings", cat, item_id, newly_filled)

        # favourite_count
        fav = data.get("favourite_count")
        if fav is not None:
            from .categorization import FAVOURITE_COUNT_CATEGORIZER
            cat = FAVOURITE_COUNT_CATEGORIZER.categorize(fav)
            if cat:
                self._add_to_dict_bucket("fetched_beatmapset_favourite_counts", cat, item_id, newly_filled)

        # play_count
        pc = data.get("play_count")
        if pc is not None:
            from .categorization import PLAY_COUNT_CATEGORIZER
            cat = PLAY_COUNT_CATEGORIZER.categorize(pc)
            if cat:
                self._add_to_dict_bucket("fetched_beatmapset_play_counts", cat, item_id, newly_filled)

        # description
        desc = data.get("description")
        if desc:
            desc_str = desc.get("description", "") if isinstance(desc, dict) else str(desc)
            if desc_str and desc_str.strip():
                self._set_bool_bucket("fetched_beatmapset_has_description", True, newly_filled)

        # pack_tags
        if data.get("pack_tags"):
            self._set_bool_bucket("fetched_beatmapset_has_pack_tags", True, newly_filled)

        # video
        if data.get("video"):
            self._set_bool_bucket("fetched_beatmapset_videos", True, newly_filled)

        # storyboard
        if data.get("storyboard"):
            self._set_bool_bucket("fetched_beatmapset_storyboards", True, newly_filled)

        # discussion_enabled
        if data.get("discussion_enabled") is not None:
            self._set_bool_bucket("fetched_beatmapset_discussions", True, newly_filled)

        # hype
        if data.get("hype") is not None:
            self._set_bool_bucket("fetched_beatmapset_hype", True, newly_filled)

        # nominations
        noms = data.get("current_nominations")
        if noms and isinstance(noms, dict):
            if noms.get("nominators"):
                self._set_bool_bucket("fetched_beatmapset_nominations", True, newly_filled)

        # sr_gaps / hit_lengths from beatmaps within the beatmapset
        beatmaps = data.get("beatmaps", [])
        has_sr_gaps = False
        has_hit_lengths = False
        for bm in beatmaps:
            if bm.get("difficulty_rating") is not None:
                has_sr_gaps = True
            if bm.get("hit_length") is not None:
                has_hit_lengths = True
        if has_sr_gaps:
            self._set_bool_bucket("fetched_beatmapset_sr_gaps", True, newly_filled)
        if has_hit_lengths:
            self._set_bool_bucket("fetched_beatmapset_hit_lengths", True, newly_filled)

    def _classify_user(self, data: dict, item_id: int, newly_filled: dict[str, set[int]]) -> None:
        """Classify user data into buckets."""
        # country_code
        cc = data.get("country_code")
        if cc:
            self._add_to_dict_bucket("fetched_country_codes", cc, item_id, newly_filled)

        # is_restricted
        restricted = data.get("is_restricted", False)
        self._add_to_dict_bucket("fetched_restricted_users", bool(restricted), item_id, newly_filled)

    def _add_to_dict_bucket(self, bucket_name: str, key: Any, item_id: int, newly_filled: dict[str, set[int]]) -> None:
        """Add an item to a dict-type bucket."""
        if bucket_name not in self._data:
            self._data[bucket_name] = {}
        if key not in self._data[bucket_name]:
            self._data[bucket_name][key] = set()
        self._data[bucket_name][key].add(item_id)
        if len(self._data[bucket_name][key]) == 1:
            newly_filled.setdefault(bucket_name, set()).add(item_id)

    def _add_to_set_bucket(self, bucket_name: str, key: Any, item_id: int, newly_filled: dict[str, set[int]]) -> None:
        """Add an item to a set-type bucket."""
        if bucket_name not in self._data:
            self._data[bucket_name] = set()
        self._data[bucket_name].add(key)
        if len(self._data[bucket_name]) == 1:
            newly_filled.setdefault(bucket_name, set()).add(item_id)

    def _set_bool_bucket(self, bucket_name: str, value: bool, newly_filled: dict[str, set[int]]) -> None:
        """Set a bool-type bucket."""
        if bucket_name not in self._data:
            self._data[bucket_name] = False
        if not self._data[bucket_name] and value:
            self._data[bucket_name] = True
            newly_filled.setdefault(bucket_name, set()).add(bucket_name)

    def is_covered(self, bucket_name: str, category: Any = None) -> bool:
        """Check if a bucket meets minimum coverage.

        Args:
            bucket_name: Name of the bucket
            category: Optional category key (for DICT type buckets)

        Returns:
            True if bucket is covered
        """
        bucket = self._buckets.get(bucket_name)
        if not bucket:
            return True

        data = self._data.get(bucket_name)
        if data is None:
            return True

        if bucket.bucket_type == BucketType.SET:
            return len(data) >= bucket.min_coverage

        elif bucket.bucket_type == BucketType.DICT:
            if category is not None:
                cat_data = data.get(category)
                if cat_data is None:
                    return False
                return len(cat_data) >= bucket.min_coverage
            # Check all categories
            if not data:
                return False
            for cat_data in data.values():
                if isinstance(cat_data, set) and len(cat_data) < bucket.min_coverage:
                    return False
            return True

        elif bucket.bucket_type == BucketType.BOOL:
            return bool(data)

        return False

    def bucket_urgency(self, bucket_name: str, category: Any = None) -> float:
        """Compute urgency weight for a bucket (0 = satisfied, >0 = needs work).

        Args:
            bucket_name: Name of the bucket
            category: Optional category key

        Returns:
            Urgency weight
        """
        if self.is_covered(bucket_name, category):
            return 0.0

        bucket = self._buckets.get(bucket_name)
        if not bucket:
            return 0.0

        rarity = bucket.rarity_weight
        data = self._data.get(bucket_name)
        if data is None:
            return 0.0

        if bucket.bucket_type == BucketType.SET:
            count = len(data)
        elif bucket.bucket_type == BucketType.DICT:
            if category is not None:
                cat_data = data.get(category)
                count = len(cat_data) if cat_data else 0
            else:
                count = min((len(v) for v in data.values() if isinstance(v, set)), default=0)
        elif bucket.bucket_type == BucketType.BOOL:
            count = 1 if data else 0
        else:
            count = 0

        if count == 0:
            return rarity * 2.0
        elif count < bucket.min_coverage:
            return rarity * 1.0
        return 0.0

    def total_uncovered(self) -> tuple[int, int]:
        """Count total number of uncovered bucket entries.

        Returns:
            Tuple of (total_uncovered, rare_uncovered)
        """
        count = 0
        rare_count = 0

        for bucket_name, bucket in self._buckets.items():
            if bucket.rarity_weight < 2.0:
                if not self.is_covered(bucket_name):
                    count += 1
            else:
                if not self.is_covered(bucket_name):
                    count += 1
                    rare_count += 1

        return count, rare_count

    def all_covered(self) -> bool:
        """Check if all buckets meet minimum coverage.

        Returns:
            True if all buckets are covered
        """
        count, _ = self.total_uncovered()
        return count == 0

    def get_status(self) -> dict[str, dict]:
        """Get current coverage status for all buckets.

        Returns:
            Dictionary of {bucket_name: {category: bool}}
        """
        status: dict[str, dict] = {}

        for bucket_name, bucket in self._buckets.items():
            data = self._data.get(bucket_name, {})

            if bucket.bucket_type == BucketType.SET:
                status[bucket_name] = {str(k): True for k in data}
            elif bucket.bucket_type == BucketType.DICT:
                status[bucket_name] = {
                    str(k): len(v) >= bucket.min_coverage
                    for k, v in data.items()
                }
            elif bucket.bucket_type == BucketType.BOOL:
                status[bucket_name] = {"covered": bool(data)}

        return status

    def get_coverage_report(self) -> dict:
        """Get full coverage report with counts and IDs.

        Returns:
            Coverage report dictionary
        """
        from .search_test_constants import GENRE_NAMES, LANGUAGE_NAMES, BEATMAP_MODE_NAMES, BEATMAP_STATUS_NAMES

        report = {}

        for bucket_name, bucket in self._buckets.items():
            data = self._data.get(bucket_name, {})

            if bucket.bucket_type == BucketType.SET:
                report[bucket_name] = sorted(data)[:20]
            elif bucket.bucket_type == BucketType.DICT:
                if "genre" in bucket_name:
                    report[bucket_name] = {
                        gid: {"name": GENRE_NAMES.get(gid, "Unknown"), "count": len(ids), "ids": sorted(ids)}
                        for gid, ids in data.items()
                    }
                elif "language" in bucket_name:
                    report[bucket_name] = {
                        lid: {"name": LANGUAGE_NAMES.get(lid, "Unknown"), "count": len(ids), "ids": sorted(ids)}
                        for lid, ids in data.items()
                    }
                elif "mode" in bucket_name:
                    report[bucket_name] = {
                        m: {"name": BEATMAP_MODE_NAMES.get(m, "Unknown"), "count": len(ids), "ids": sorted(ids)}
                        for m, ids in data.items()
                    }
                elif "status" in bucket_name and "beatmap" in bucket_name:
                    report[bucket_name] = {
                        s: {"name": BEATMAP_STATUS_NAMES.get(int(s), s), "count": len(ids), "ids": sorted(ids)}
                        for s, ids in data.items()
                    }
                else:
                    report[bucket_name] = {
                        cat: {"count": len(ids), "ids": sorted(ids)}
                        for cat, ids in data.items()
                    }
            elif bucket.bucket_type == BucketType.BOOL:
                report[bucket_name] = bool(data)

        return report
