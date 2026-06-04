import json
import random
from datetime import datetime, timezone

from app.redis import RedisClient
from app.osu_api.client.osu_api_client import OsuAPIClient
from app.osu_api.enums import ScoreType, Ruleset

from .utils import (
    load_metadata,
    save_metadata,
    get_fixture_path,
    RULESETS,
    SCORE_TYPES,
    ID_RANGES,
)

MAX_RETRIES = 5


class FixtureDataFetcher:
    def __init__(self, rc: RedisClient, id_ranges: dict | None = None):
        self.rc = rc
        self.oac = OsuAPIClient(rc)
        self.logger = None
        self.metadata = load_metadata()
        self.failed_ids = self.metadata.get("failed_ids", {
            "beatmaps": [],
            "beatmapsets": [],
            "users": {r: [] for r in RULESETS},
        })
        self.id_ranges = id_ranges or self.metadata.get("id_ranges", ID_RANGES)

    async def fetch_beatmaps(self, count: int) -> int:
        path = get_fixture_path("beatmaps")
        fetched = 0

        for _ in range(count):
            beatmap_id = self._get_random_id("beatmaps")
            retries = 0
            while retries < MAX_RETRIES:
                try:
                    data = await self.oac.get_beatmap(beatmap_id)
                    filepath = path / f"beatmap_{beatmap_id}.json"
                    with open(filepath, "w") as f:
                        json.dump(data, f, indent=2)
                    fetched += 1
                    break
                except Exception as e:
                    self.logger.debug(f"Failed to fetch beatmap {beatmap_id} (retry {retries + 1}/{MAX_RETRIES}): {e}")
                    self._add_failed_id("beatmaps", beatmap_id)
                    retries += 1
                    beatmap_id = self._get_random_id("beatmaps")

        self.metadata["samples"]["beatmaps"]["count"] += fetched
        self.metadata["samples"]["beatmaps"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        save_metadata(self.metadata)
        return fetched

    async def fetch_beatmapsets(self, count: int) -> int:
        path = get_fixture_path("beatmapsets")
        fetched = 0

        for _ in range(count):
            beatmapset_id = self._get_random_id("beatmapsets")
            retries = 0
            while retries < MAX_RETRIES:
                try:
                    data = await self.oac.get_beatmapset(beatmapset_id)
                    filepath = path / f"beatmapset_{beatmapset_id}.json"
                    with open(filepath, "w") as f:
                        json.dump(data, f, indent=2)
                    fetched += 1
                    break
                except Exception as e:
                    self.logger.debug(f"Failed to fetch beatmapset {beatmapset_id} (retry {retries + 1}/{MAX_RETRIES}): {e}")
                    self._add_failed_id("beatmapsets", beatmapset_id)
                    retries += 1
                    beatmapset_id = self._get_random_id("beatmapsets")

        self.metadata["samples"]["beatmapsets"]["count"] += fetched
        self.metadata["samples"]["beatmapsets"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        save_metadata(self.metadata)
        return fetched

    async def fetch_users(
        self,
        users_osu: int,
        users_taiko: int,
        users_fruits: int,
        users_mania: int,
    ) -> dict[str, int]:
        path = get_fixture_path("users")
        fetched = {r: 0 for r in RULESETS}

        ruleset_counts = {
            "osu": users_osu,
            "taiko": users_taiko,
            "fruits": users_fruits,
            "mania": users_mania,
        }

        for ruleset in RULESETS:
            ruleset_path = path / ruleset
            ruleset_path.mkdir(parents=True, exist_ok=True)
            count = ruleset_counts[ruleset]

            for _ in range(count):
                user_id = self._get_random_id(f"users.{ruleset}")
                mode = getattr(Ruleset, ruleset.upper()).value
                retries = 0
                while retries < MAX_RETRIES:
                    try:
                        data = await self.oac.get_user(user_id, Ruleset(mode))
                        filepath = ruleset_path / f"user_{user_id}_{ruleset}.json"
                        with open(filepath, "w") as f:
                            json.dump(data, f, indent=2)
                        fetched[ruleset] += 1
                        break
                    except Exception as e:
                        self.logger.debug(f"Failed to fetch user {user_id} ({ruleset}) (retry {retries + 1}/{MAX_RETRIES}): {e}")
                        self._add_failed_id(f"users.{ruleset}", user_id)
                        retries += 1
                        user_id = self._get_random_id(f"users.{ruleset}")

        self.metadata["samples"]["users"]["count"] += sum(fetched.values())
        self.metadata["samples"]["users"]["per_ruleset"] = {
            r: self.metadata["samples"]["users"]["per_ruleset"].get(r, 0) + fetched[r] for r in RULESETS
        }
        self.metadata["samples"]["users"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        save_metadata(self.metadata)
        return fetched

    async def fetch_scores(
        self,
        scores_best: int,
        scores_firsts: int,
        scores_recent: int,
    ) -> dict[str, int]:
        path = get_fixture_path("scores")
        fetched = {t: 0 for t in SCORE_TYPES}

        type_counts = {
            "best": scores_best,
            "firsts": scores_firsts,
            "recent": scores_recent,
        }

        for score_type in SCORE_TYPES:
            type_path = path / score_type
            type_path.mkdir(parents=True, exist_ok=True)
            count = type_counts[score_type]

            for _ in range(count):
                user_id = self._get_random_id("users")
                mode = Ruleset.OSU
                score_type_enum = getattr(ScoreType, score_type.upper())
                retries = 0
                while retries < MAX_RETRIES:
                    try:
                        data = await self.oac.get_user_scores(user_id, score_type_enum, mode=mode)
                        filepath = type_path / f"scores_{user_id}_{score_type}.json"
                        with open(filepath, "w") as f:
                            json.dump(data, f, indent=2)
                        fetched[score_type] += 1
                        break
                    except Exception as e:
                        self.logger.debug(f"Failed to fetch scores for user {user_id} ({score_type}) (retry {retries + 1}/{MAX_RETRIES}): {e}")
                        self._add_failed_id("users", user_id)
                        retries += 1
                        user_id = self._get_random_id("users")

        self.metadata["samples"]["scores"]["count"] += sum(fetched.values())
        self.metadata["samples"]["scores"]["per_type"] = {
            t: self.metadata["samples"]["scores"]["per_type"].get(t, 0) + fetched[t] for t in SCORE_TYPES
        }
        self.metadata["samples"]["scores"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        save_metadata(self.metadata)
        return fetched

    async def fetch_beatmap_scores(self, count: int) -> int:
        path = get_fixture_path("beatmap_scores")
        fetched = 0

        for _ in range(count):
            beatmap_id = self._get_random_id("beatmaps")
            retries = 0
            while retries < MAX_RETRIES:
                try:
                    data = await self.oac.get_beatmap_scores(beatmap_id, limit=1)
                    filepath = path / f"beatmap_scores_{beatmap_id}.json"
                    with open(filepath, "w") as f:
                        json.dump(data, f, indent=2)
                    fetched += 1
                    break
                except Exception as e:
                    self.logger.debug(f"Failed to fetch beatmap scores {beatmap_id} (retry {retries + 1}/{MAX_RETRIES}): {e}")
                    self._add_failed_id("beatmaps", beatmap_id)
                    retries += 1
                    beatmap_id = self._get_random_id("beatmaps")

        self.metadata["samples"]["beatmap_scores"]["count"] += fetched
        self.metadata["samples"]["beatmap_scores"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        save_metadata(self.metadata)
        return fetched

    async def fetch_beatmap_attributes(self, count: int) -> int:
        path = get_fixture_path("beatmap_attributes")
        fetched = 0

        for _ in range(count):
            beatmap_id = self._get_random_id("beatmaps")
            mods = random.choice([0, 1, 2, 64, 128, 256])
            retries = 0
            while retries < MAX_RETRIES:
                try:
                    data = await self.oac.get_beatmap_attributes(beatmap_id, mods)
                    filepath = path / f"beatmap_attrs_{beatmap_id}_mods{mods}.json"
                    with open(filepath, "w") as f:
                        json.dump(data, f, indent=2)
                    fetched += 1
                    break
                except Exception as e:
                    self.logger.debug(f"Failed to fetch beatmap attributes {beatmap_id} (retry {retries + 1}/{MAX_RETRIES}): {e}")
                    self._add_failed_id("beatmaps", beatmap_id)
                    retries += 1
                    beatmap_id = self._get_random_id("beatmaps")

        self.metadata["samples"]["beatmap_attributes"]["count"] += fetched
        self.metadata["samples"]["beatmap_attributes"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        save_metadata(self.metadata)
        return fetched

    async def fetch_all(self, sample_counts: dict) -> dict:
        self.logger.info("Fetching fixture data from osu! API...")
        
        users = sample_counts.get("users", {})
        scores = sample_counts.get("scores", {})
        
        results = {
            "beatmaps": await self.fetch_beatmaps(sample_counts.get("beatmaps", 0)),
            "beatmapsets": await self.fetch_beatmapsets(sample_counts.get("beatmapsets", 0)),
            "users": await self.fetch_users(
                users.get("osu", 0),
                users.get("taiko", 0),
                users.get("fruits", 0),
                users.get("mania", 0),
            ),
            "scores": await self.fetch_scores(
                scores.get("best", 0),
                scores.get("firsts", 0),
                scores.get("recent", 0),
            ),
            "beatmap_scores": await self.fetch_beatmap_scores(sample_counts.get("beatmap_scores", 0)),
            "beatmap_attributes": await self.fetch_beatmap_attributes(sample_counts.get("beatmap_attributes", 0)),
        }
        self.logger.info(f"Fixture data fetch complete: {results}")
        return results

    def _get_random_id(self, category: str) -> int:
        range_config = self.id_ranges.get(category, self.id_ranges.get(category.split(".")[0], {"min": 1, "max": 1000000}))
        min_id = range_config.get("min", 1)
        max_id = range_config.get("max", 1000000)
        
        failed_list = self.failed_ids.get(category, [])
        
        for _ in range(MAX_RETRIES * 2):
            candidate = random.randint(min_id, max_id)
            if candidate not in failed_list:
                return candidate
        
        return random.randint(min_id, max_id)

    def _add_failed_id(self, category: str, id_: int) -> None:
        if category not in self.failed_ids:
            self.failed_ids[category] = []
        if id_ not in self.failed_ids[category]:
            self.failed_ids[category].append(id_)
            if len(self.failed_ids[category]) > 1000:
                self.failed_ids[category] = self.failed_ids[category][-1000:]
