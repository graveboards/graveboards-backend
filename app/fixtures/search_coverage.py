"""Adaptive coverage engine for search test fixtures.

Uses a priority queue of fetch actions to minimize API calls while
filling all coverage buckets. After each fetch, the engine re-evaluates
which action has the highest expected information gain and picks that next.

This replaces the old fixed 4-round approach (30/30/20/30) with an
adaptive loop that stops as soon as all buckets are satisfied.
"""
import heapq
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

# Rarity weights: how hard each bucket is to fill via random fetching.
# Higher = rarer = should be prioritized when uncovered.
# These are constants that can be tweaked later if needed.
BUCKET_RARITY: dict[str, float] = {
    # Beatmapset buckets - easy to medium
    "fetched_beatmapset_genres": 1.0,
    "fetched_beatmapset_languages": 1.0,
    "fetched_beatmapset_statuses": 1.0,
    "fetched_beatmapset_ratings": 1.0,
    "fetched_beatmapset_favourite_counts": 1.0,
    "fetched_beatmapset_play_counts": 1.0,
    "fetched_beatmapset_has_description": 1.0,
    "fetched_beatmapset_has_pack_tags": 1.0,
    "fetched_beatmapset_videos": 1.0,
    "fetched_beatmapset_storyboards": 1.0,
    "fetched_beatmapset_discussions": 1.0,
    "fetched_beatmapset_hype": 1.0,
    "fetched_beatmapset_nominations": 1.0,
    "fetched_beatmapset_sr_gaps": 1.0,
    "fetched_beatmapset_hit_lengths": 1.0,

    # Beatmapset buckets - rare
    "fetched_beatmapset_nsfw": 2.5,

    # Beatmap buckets
    "fetched_beatmap_modes": 1.0,
    "fetched_beatmap_statuses": 1.0,
    "fetched_beatmap_difficulties": 1.0,
    "fetched_beatmap_playcounts": 1.0,
    "fetched_beatmap_bpm": 1.0,
    "fetched_beatmap_accuracy": 1.0,
    "fetched_beatmap_hit_lengths": 1.0,
    "fetched_beatmap_max_combos": 1.0,
    "fetched_beatmap_drain": 1.0,
    "fetched_beatmap_ar": 1.0,
    "fetched_beatmap_cs": 1.0,
    "fetched_beatmap_versions": 1.0,

    # User buckets
    "fetched_country_codes": 1.0,
    "fetched_restricted_users": 3.0,
}

SHORT_NAMES: dict[str, str] = {
    "fetched_beatmapset_genres": "bs_genre",
    "fetched_beatmapset_languages": "bs_lang",
    "fetched_beatmapset_nsfw": "bs_nsfw",
    "fetched_beatmapset_statuses": "bs_status",
    "fetched_beatmapset_ratings": "bs_rating",
    "fetched_beatmapset_favourite_counts": "bs_favs",
    "fetched_beatmapset_play_counts": "bs_plays",
    "fetched_beatmapset_has_description": "bs_desc",
    "fetched_beatmapset_has_pack_tags": "bs_pack",
    "fetched_beatmapset_videos": "bs_video",
    "fetched_beatmapset_storyboards": "bs_story",
    "fetched_beatmapset_discussions": "bs_disc",
    "fetched_beatmapset_hype": "bs_hype",
    "fetched_beatmapset_nominations": "bs_noms",
    "fetched_beatmapset_sr_gaps": "bs_sr",
    "fetched_beatmapset_hit_lengths": "bs_hitlen",
    "fetched_beatmap_modes": "bm_mode",
    "fetched_beatmap_statuses": "bm_status",
    "fetched_beatmap_difficulties": "bm_diff",
    "fetched_beatmap_playcounts": "bm_plays",
    "fetched_beatmap_bpm": "bm_bpm",
    "fetched_beatmap_accuracy": "bm_acc",
    "fetched_beatmap_hit_lengths": "bm_hitlen",
    "fetched_beatmap_max_combos": "bm_combo",
    "fetched_beatmap_drain": "bm_drain",
    "fetched_beatmap_ar": "bm_ar",
    "fetched_beatmap_cs": "bm_cs",
    "fetched_beatmap_versions": "bm_ver",
    "fetched_country_codes": "user_country",
    "fetched_restricted_users": "user_restricted",
}

RARE_BUCKET_THRESHOLD = 2.0


@runtime_checkable
class FetchAction(Protocol):
    """A fetch action that can fill certain coverage buckets."""

    name: str
    affected_buckets: list[str]
    cost: int
    rarity_weight: float

    async def execute(self) -> dict[str, set[int]]:
        """Execute the fetch and return {bucket_key: set_of_new_ids}."""


@dataclass
class HeapEntry:
    """Entry in the priority queue. Lower priority_value = higher priority."""
    priority_value: float
    sequence: int
    action: Any

    def __lt__(self, other: "HeapEntry") -> bool:
        return self.priority_value < other.priority_value


class CoverageTracker:
    """Tracks coverage state and computes action priorities.

    Wraps the set-based coverage tracking from SearchTestFixtureFetcher
    and provides priority calculation for the adaptive fetch loop.
    """

    def __init__(self, fetcher: Any, min_per_category: int = 1):
        self.fetcher = fetcher
        self.min_per_category = min_per_category

    def is_bucket_covered(self, bucket_key: str, category: Any = None) -> bool:
        """Check if a bucket meets the minimum coverage threshold."""
        attr = getattr(self.fetcher, bucket_key, None)
        if attr is None:
            return True

        if isinstance(attr, set):
            return len(attr) >= self.min_per_category

        if isinstance(attr, dict):
            if category is not None:
                cat_data = attr.get(category)
                if cat_data is None:
                    return False
                return len(cat_data) >= self.min_per_category
            # Check all categories
            if not attr:
                return False
            for cat_data in attr.values():
                if isinstance(cat_data, set) and len(cat_data) < self.min_per_category:
                    return False
            return True

        if isinstance(attr, bool):
            return attr

        return False

    def bucket_urgency(self, bucket_key: str, category: Any = None) -> float:
        """Compute urgency weight for a bucket (0 = satisfied, >0 = needs work)."""
        if self.is_bucket_covered(bucket_key, category):
            return 0.0

        rarity = BUCKET_RARITY.get(bucket_key, 1.0)

        attr = getattr(self.fetcher, bucket_key, None)
        if attr is None:
            return 0.0

        if isinstance(attr, set):
            count = len(attr)
        elif isinstance(attr, dict):
            if category is not None:
                cat_data = attr.get(category)
                count = len(cat_data) if cat_data else 0
            else:
                count = min((len(v) for v in attr.values() if isinstance(v, set)), default=0)
        elif isinstance(attr, bool):
            count = 1 if attr else 0
        else:
            count = 0

        # Inverse relationship: fewer items = higher urgency
        if count == 0:
            return rarity * 2.0
        elif count < self.min_per_category:
            return rarity * 1.0
        return 0.0

    def total_uncovered(self) -> int:
        """Count total number of uncovered bucket entries."""
        count = 0
        rare_uncovered = 0
        for bucket_key in BUCKET_RARITY:
            attr = getattr(self.fetcher, bucket_key, None)
            if attr is None:
                continue

            if isinstance(attr, set):
                if len(attr) < self.min_per_category:
                    count += 1
                    if BUCKET_RARITY.get(bucket_key, 0) >= RARE_BUCKET_THRESHOLD:
                        rare_uncovered += 1
            elif isinstance(attr, dict):
                for cat_data in attr.values():
                    if isinstance(cat_data, set) and len(cat_data) < self.min_per_category:
                        count += 1
                        if BUCKET_RARITY.get(bucket_key, 0) >= RARE_BUCKET_THRESHOLD:
                            rare_uncovered += 1
            elif isinstance(attr, bool):
                if not attr:
                    count += 1
                    if BUCKET_RARITY.get(bucket_key, 0) >= RARE_BUCKET_THRESHOLD:
                        rare_uncovered += 1
        return count, rare_uncovered

    def compute_action_priority(self, action: FetchAction) -> float:
        """Compute priority for a fetch action.

        Priority = (urgency_sum + rare_bonus) / cost.
        Rare buckets (high rarity weight) get extra priority when uncovered.
        Higher priority = more valuable to execute next.
        """
        total_urgency = 0.0
        rare_bonus = 0.0
        for bucket_key in action.affected_buckets:
            urgency = self.bucket_urgency(bucket_key)
            if urgency > 0:
                rarity = BUCKET_RARITY.get(bucket_key, 1.0)
                total_urgency += urgency
                if rarity >= RARE_BUCKET_THRESHOLD:
                    rare_bonus += rarity * 10.0

        if action.cost == 0:
            return 0.0
        return (total_urgency + rare_bonus) / action.cost

    def all_covered(self) -> bool:
        """Check if all buckets meet minimum coverage."""
        count, _ = self.total_uncovered()
        return count == 0


class SearchTestFetchAction:
    """Concrete fetch actions for the adaptive loop."""

    def __init__(self, fetcher: Any):
        self.fetcher = fetcher

    async def fetch_beatmapsets(self) -> dict[str, set[int]]:
        """Fetch one random beatmapset via search."""
        import random
        from app.fixtures.paths import get_fixture_path

        search_statuses = [1, 4, 0, -1]
        status = search_statuses[random.randint(0, len(search_statuses) - 1)]
        page = random.randint(1, 100)

        try:
            data = await self.fetcher.oac.search_beatmapsets(page=page, status=status)
        except Exception:
            return {}

        beatmapsets = data.get("beatmapsets", [])
        if not beatmapsets:
            return {}

        bs_data = beatmapsets[0]
        bs_id = bs_data.get("beatmapset_id") or bs_data.get("id")
        if not bs_id:
            return {}

        try:
            bs_full = await self.fetcher.oac.get_beatmapset(bs_id)
        except Exception:
            return {}

        filepath = get_fixture_path("beatmapsets") / f"beatmapset_{bs_id}.json"
        import json
        with open(filepath, "w") as f:
            json.dump(bs_full, f, indent=2)

        classifications = self.fetcher._classify_beatmapset(bs_full, bs_id)
        result: dict[str, set[int]] = {}
        for bucket_name, cats in classifications.items():
            if isinstance(cats, dict):
                for cat, ids in cats.items():
                    if len(ids) == 1:
                        result.setdefault(bucket_name, set()).update(ids)
            elif isinstance(cats, set) and len(cats) == 1:
                result.setdefault(bucket_name, set()).update(cats)

        self.fetcher.metadata["samples"]["beatmapsets"]["count"] = (
            self.fetcher.metadata["samples"]["beatmapsets"].get("count", 0) + 1
        )
        return result

    async def fetch_beatmap(self) -> dict[str, set[int]]:
        """Fetch one random beatmap."""
        from app.fixtures.utils import get_fixture_path

        beatmap_id = await self.fetcher._get_random_id("beatmaps", avoid_failed=True)

        try:
            beatmap_data = await self.fetcher.oac.get_beatmap(beatmap_id)
        except Exception:
            await self.fetcher._add_failed_id("beatmaps", beatmap_id)
            return {}

        filepath = get_fixture_path("beatmaps") / f"beatmap_{beatmap_id}.json"
        import json
        with open(filepath, "w") as f:
            json.dump(beatmap_data, f, indent=2)

        classifications = self.fetcher._classify_beatmap(beatmap_data, beatmap_id)
        result: dict[str, set[int]] = {}
        for bucket_name, cats in classifications.items():
            if isinstance(cats, dict):
                for cat, ids in cats.items():
                    if len(ids) == 1:
                        result.setdefault(bucket_name, set()).update(ids)
            elif isinstance(cats, set) and len(cats) == 1:
                result.setdefault(bucket_name, set()).update(cats)

        self.fetcher.metadata["samples"]["beatmaps"]["count"] = (
            self.fetcher.metadata["samples"]["beatmaps"].get("count", 0) + 1
        )
        return result

    async def fetch_user(self) -> dict[str, set[int]]:
        """Fetch one random user from rankings."""
        from app.fixtures.utils import get_fixture_path

        try:
            data = await self.fetcher.oac.get_rankings(
                ruleset="osu", mode="performance", cursor_page=1, limit=1
            )
        except Exception:
            return {}

        players = data.get("ranking", [])
        if not players:
            return {}

        user = players[0].get("user")
        if not user:
            return {}
        user_id = user.get("id")
        if not user_id:
            return {}

        try:
            user_data = await self.fetcher.oac.get_user(user_id, "osu")
        except Exception:
            await self.fetcher._add_failed_id("users.osu", user_id)
            return {}

        ruleset_path = get_fixture_path("users") / "osu"
        ruleset_path.mkdir(parents=True, exist_ok=True)
        filepath = ruleset_path / f"user_{user_id}_osu.json"
        import json
        with open(filepath, "w") as f:
            json.dump(user_data, f, indent=2)

        classifications = self.fetcher._classify_user(user_data, user_id)
        result: dict[str, set[int]] = {}
        for bucket_name, cats in classifications.items():
            if isinstance(cats, dict):
                for cat, ids in cats.items():
                    if len(ids) == 1:
                        result.setdefault(bucket_name, set()).update(ids)

        self.fetcher.metadata["samples"]["users"]["count"] = (
            self.fetcher.metadata["samples"]["users"].get("count", 0) + 1
        )
        self.fetcher.metadata["samples"]["users"]["per_ruleset"]["osu"] = (
            self.fetcher.metadata["samples"]["users"]["per_ruleset"].get("osu", 0) + 1
        )
        return result

    async def fetch_special_beatmapset(self) -> dict[str, set[int]]:
        """Fetch one special beatmapset (NSFW, graveyard, restricted)."""
        import random
        from app.fixtures.paths import get_fixture_path
        from app.fixtures.search_test_known_ids import (
            RESTRICTED_BEATMAPSET_IDS,
            NSFW_BEATMAPSET_IDS,
        )

        candidate_ids = (
            list(RESTRICTED_BEATMAPSET_IDS)
            + list(NSFW_BEATMAPSET_IDS)
        )
        while len(candidate_ids) < 50:
            candidate_ids.append(random.randint(1, 20000000))
        random.shuffle(candidate_ids)

        for bs_id in candidate_ids:
            try:
                bs_full = await self.fetcher.oac.get_beatmapset(bs_id)
            except Exception:
                await self.fetcher._add_failed_id("beatmapsets", bs_id)
                continue

            filepath = get_fixture_path("beatmapsets") / f"beatmapset_{bs_id}.json"
            import json
            with open(filepath, "w") as f:
                json.dump(bs_full, f, indent=2)

            user = bs_full.get("user") or {}
            if user.get("is_deleted") or (not user.get("is_active") and user.get("id")):
                self.fetcher.fetched_restricted_users[True].add(bs_id)

            classifications = self.fetcher._classify_beatmapset(bs_full, bs_id)
            result: dict[str, set[int]] = {}
            for bucket_name, cats in classifications.items():
                if isinstance(cats, dict):
                    for cat, ids in cats.items():
                        if len(ids) == 1:
                            result.setdefault(bucket_name, set()).update(ids)
                elif isinstance(cats, set) and len(cats) == 1:
                    result.setdefault(bucket_name, set()).update(cats)

            self.fetcher.metadata["samples"]["beatmapsets"]["count"] = (
                self.fetcher.metadata["samples"]["beatmapsets"].get("count", 0) + 1
            )
            return result

        return {}


def build_actions(fetcher: Any) -> list[FetchAction]:
    """Build the list of fetch actions with their bucket mappings."""
    actions = []

    actions.append(_make_action(
        fetcher,
        name="beatmapsets",
        execute=fetcher._adaptive_fetch_beatmapsets,
        affected_buckets=[
            "fetched_beatmapset_genres", "fetched_beatmapset_languages",
            "fetched_beatmapset_nsfw", "fetched_beatmapset_statuses",
            "fetched_beatmapset_ratings", "fetched_beatmapset_favourite_counts",
            "fetched_beatmapset_play_counts", "fetched_beatmapset_has_description",
            "fetched_beatmapset_has_pack_tags", "fetched_beatmapset_videos",
            "fetched_beatmapset_storyboards", "fetched_beatmapset_discussions",
            "fetched_beatmapset_hype", "fetched_beatmapset_nominations",
            "fetched_beatmapset_sr_gaps", "fetched_beatmapset_hit_lengths",
            "fetched_beatmap_modes", "fetched_beatmap_statuses",
            "fetched_beatmap_difficulties", "fetched_beatmap_playcounts",
        ],
        cost=2,
    ))

    actions.append(_make_action(
        fetcher,
        name="beatmaps",
        execute=fetcher._adaptive_fetch_beatmaps,
        affected_buckets=[
            "fetched_beatmap_modes", "fetched_beatmap_statuses",
            "fetched_beatmap_difficulties", "fetched_beatmap_playcounts",
            "fetched_beatmap_bpm", "fetched_beatmap_accuracy",
            "fetched_beatmap_hit_lengths", "fetched_beatmap_max_combos",
            "fetched_beatmap_drain", "fetched_beatmap_ar", "fetched_beatmap_cs",
            "fetched_beatmap_versions",
        ],
        cost=1,
    ))

    actions.append(_make_action(
        fetcher,
        name="users",
        execute=fetcher._adaptive_fetch_users,
        affected_buckets=[
            "fetched_country_codes", "fetched_restricted_users",
        ],
        cost=1,
    ))

    actions.append(_make_action(
        fetcher,
        name="special",
        execute=fetcher._adaptive_fetch_special,
        affected_buckets=[
            "fetched_beatmapset_nsfw", "fetched_beatmapset_statuses",
            "fetched_beatmapset_ratings", "fetched_beatmapset_favourite_counts",
            "fetched_beatmapset_play_counts", "fetched_beatmapset_has_description",
            "fetched_beatmapset_videos", "fetched_beatmapset_storyboards",
            "fetched_beatmap_modes", "fetched_beatmap_difficulties",
        ],
        cost=1,
    ))

    return actions


def _make_action(fetcher: Any, name: str, execute, affected_buckets: list[str], cost: int) -> FetchAction:
    """Create a fetch action with the required interface."""
    from types import SimpleNamespace
    action = SimpleNamespace()
    action.name = name
    action.affected_buckets = affected_buckets
    action.cost = cost
    action.execute = execute
    return action


async def adaptive_fetch_loop(
    fetcher: Any,
    min_per_category: int = 1,
    max_total: int = 500,
) -> dict[str, Any]:
    """Run the adaptive priority-based fetch loop.

    After each fetch, re-evaluates which action has the highest expected
    information gain and picks that next. Stops when all buckets are
    satisfied or max_total API calls exhausted.
    """
    tracker = CoverageTracker(fetcher, min_per_category=min_per_category)
    actions = build_actions(fetcher)

    total_calls = 0
    newly_filled: dict[str, int] = {}
    wasted_calls = 0
    sequence = 0
    heap: list[HeapEntry] = []

    uncovered_count, rare_count = tracker.total_uncovered()
    initial_uncovered = uncovered_count
    fetcher.logger.info(
        f"Search test fetch: {uncovered_count} uncovered buckets "
        f"({rare_count} rare), max {max_total} API calls, "
        f"min {min_per_category} per category"
    )

    def _reheap():
        nonlocal sequence
        heap.clear()
        for action in actions:
            priority = tracker.compute_action_priority(action)
            if priority > 0:
                entry = HeapEntry(
                    priority_value=-priority,  # negate for max-heap behavior
                    sequence=sequence,
                    action=action,
                )
                heapq.heappush(heap, entry)
                sequence += 1

    _reheap()
    available = [a.name for a in actions if tracker.compute_action_priority(a) > 0]
    fetcher.logger.info(f"Actions available: {', '.join(available)}")

    last_progress_log = 0
    buckets_at_last_progress = initial_uncovered
    PROGRESS_INTERVAL = 10

    while heap and total_calls < max_total:
        entry = heapq.heappop(heap)
        action = entry.action

        if total_calls - last_progress_log >= PROGRESS_INTERVAL:
            uncovered_count, rare_count = tracker.total_uncovered()
            new_this_round = buckets_at_last_progress - uncovered_count
            if new_this_round < 0:
                new_this_round = 0
            fetcher.logger.info(
                f"Progress: {total_calls}/{max_total} calls | "
                f"{uncovered_count} uncovered ({rare_count} rare) | "
                f"+{new_this_round} new buckets"
            )
            last_progress_log = total_calls
            buckets_at_last_progress = uncovered_count

        target_buckets = ", ".join(SHORT_NAMES.get(b, b) for b in action.affected_buckets[:5])
        if len(action.affected_buckets) > 5:
            target_buckets += f" (+{len(action.affected_buckets) - 5} more)"

        fetcher.logger.debug(
            f"Fetching via {action.name} (priority={-entry.priority_value:.2f}, "
            f"calls={total_calls}/{max_total}) targeting: {target_buckets}"
        )

        result = await action.execute()
        total_calls += action.cost

        if result:
            fill_str = ", ".join(SHORT_NAMES.get(k, k) for k in result.keys())
            fetcher.logger.debug(
                f"  -> filled: {fill_str} ({len(result)} buckets)"
            )
        else:
            fetcher.logger.debug(f"  -> no new buckets filled")
            wasted_calls += 1

        # Count newly filled buckets
        for bucket_key, ids in result.items():
            newly_filled[bucket_key] = newly_filled.get(bucket_key, 0) + 1

        # Re-evaluate priorities
        _reheap()

        if tracker.all_covered():
            fetcher.logger.info(
                f"All {initial_uncovered} buckets covered after {total_calls} API calls"
            )
            break

    # Rare-bucket enforcement: if rare buckets remain, force users action
    uncovered_count, rare_count = tracker.total_uncovered()
    if rare_count > 0 and total_calls < max_total:
        fetcher.logger.info(
            f"Rare buckets still uncovered ({rare_count}), forcing users action..."
        )
        users_action = next((a for a in actions if a.name == "users"), None)
        if users_action:
            while rare_count > 0 and total_calls < max_total:
                fetcher.logger.debug(
                    f"Forced fetch via users (calls={total_calls}/{max_total})"
                )
                result = await users_action.execute()
                total_calls += 1
                if result:
                    fill_str = ", ".join(SHORT_NAMES.get(k, k) for k in result.keys())
                    fetcher.logger.debug(
                        f"  -> filled: {fill_str} ({len(result)} buckets)"
                    )
                else:
                    wasted_calls += 1
                    fetcher.logger.debug(f"  -> no new buckets filled")
                for bucket_key, ids in result.items():
                    newly_filled[bucket_key] = newly_filled.get(bucket_key, 0) + 1
                _reheap()
                _, rare_count = tracker.total_uncovered()

    remaining, rare_remaining = tracker.total_uncovered()
    if remaining > 0:
        rare_str = f", {rare_remaining} rare" if rare_remaining > 0 else ""
        fetcher.logger.info(
            f"Reached max calls ({max_total}). {remaining} buckets still uncovered{rare_str}, "
            f"{wasted_calls} wasted calls (no new buckets)"
        )
    else:
        fetcher.logger.info(
            f"Adaptive fetch complete: {total_calls} API calls, "
            f"{wasted_calls} wasted calls"
        )

    if newly_filled:
        top_buckets = sorted(newly_filled.items(), key=lambda x: x[1], reverse=True)[:10]
        fetcher.logger.info(
            f"Top filled buckets: {', '.join(f'{SHORT_NAMES.get(k, k)}={v}' for k, v in top_buckets)}"
        )

    fetcher._save_search_test_coverage_metadata()
    return fetcher.get_coverage_report()
