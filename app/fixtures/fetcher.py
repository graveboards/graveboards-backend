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
)


class FixtureDataFetcher:
    def __init__(self, rc: RedisClient):
        self.rc = rc
        self.oac = OsuAPIClient(rc)
        self.logger = None

    async def fetch_beatmaps(self, count: int) -> int:
        path = get_fixture_path("beatmaps")
        metadata = load_metadata()
        fetched = 0

        for _ in range(count):
            beatmap_id = random.randint(1, 1000000)
            try:
                data = await self.oac.get_beatmap(beatmap_id)
                filepath = path / f"beatmap_{beatmap_id}.json"
                with open(filepath, "w") as f:
                    json.dump(data, f, indent=2)
                fetched += 1
            except Exception as e:
                self.logger.debug(f"Failed to fetch beatmap {beatmap_id}: {e}")

        metadata["samples"]["beatmaps"]["count"] += fetched
        metadata["samples"]["beatmaps"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        save_metadata(metadata)
        return fetched

    async def fetch_beatmapsets(self, count: int) -> int:
        path = get_fixture_path("beatmapsets")
        metadata = load_metadata()
        fetched = 0

        for _ in range(count):
            beatmapset_id = random.randint(1, 100000)
            try:
                data = await self.oac.get_beatmapset(beatmapset_id)
                filepath = path / f"beatmapset_{beatmapset_id}.json"
                with open(filepath, "w") as f:
                    json.dump(data, f, indent=2)
                fetched += 1
            except Exception as e:
                self.logger.debug(f"Failed to fetch beatmapset {beatmapset_id}: {e}")

        metadata["samples"]["beatmapsets"]["count"] += fetched
        metadata["samples"]["beatmapsets"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        save_metadata(metadata)
        return fetched

    async def fetch_users(
        self,
        users_osu: int,
        users_taiko: int,
        users_fruits: int,
        users_mania: int,
    ) -> dict[str, int]:
        path = get_fixture_path("users")
        metadata = load_metadata()
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
                user_id = random.randint(1, 10000000)
                try:
                    data = await self.oac.get_user(user_id, getattr(Ruleset, ruleset.upper()))
                    filepath = ruleset_path / f"user_{user_id}_{ruleset}.json"
                    with open(filepath, "w") as f:
                        json.dump(data, f, indent=2)
                    fetched[ruleset] += 1
                except Exception as e:
                    self.logger.debug(f"Failed to fetch user {user_id} ({ruleset}): {e}")

        metadata["samples"]["users"]["count"] += sum(fetched.values())
        metadata["samples"]["users"]["per_ruleset"] = {
            r: metadata["samples"]["users"]["per_ruleset"].get(r, 0) + fetched[r] for r in RULESETS
        }
        metadata["samples"]["users"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        save_metadata(metadata)
        return fetched

    async def fetch_scores(
        self,
        scores_best: int,
        scores_firsts: int,
        scores_recent: int,
    ) -> dict[str, int]:
        path = get_fixture_path("scores")
        metadata = load_metadata()
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
                user_id = random.randint(1, 10000000)
                try:
                    data = await self.oac.get_user_scores(user_id, getattr(ScoreType, score_type.upper()))
                    filepath = type_path / f"scores_{user_id}_{score_type}.json"
                    with open(filepath, "w") as f:
                        json.dump(data, f, indent=2)
                    fetched[score_type] += 1
                except Exception as e:
                    self.logger.debug(f"Failed to fetch scores for user {user_id} ({score_type}): {e}")

        metadata["samples"]["scores"]["count"] += sum(fetched.values())
        metadata["samples"]["scores"]["per_type"] = {
            t: metadata["samples"]["scores"]["per_type"].get(t, 0) + fetched[t] for t in SCORE_TYPES
        }
        metadata["samples"]["scores"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        save_metadata(metadata)
        return fetched

    async def fetch_beatmap_scores(self, count: int) -> int:
        path = get_fixture_path("beatmap_scores")
        metadata = load_metadata()
        fetched = 0

        for _ in range(count):
            beatmap_id = random.randint(1, 1000000)
            try:
                data = await self.oac.get_beatmap_scores(beatmap_id)
                filepath = path / f"beatmap_scores_{beatmap_id}.json"
                with open(filepath, "w") as f:
                    json.dump(data, f, indent=2)
                fetched += 1
            except Exception as e:
                self.logger.debug(f"Failed to fetch beatmap scores {beatmap_id}: {e}")

        metadata["samples"]["beatmap_scores"]["count"] += fetched
        metadata["samples"]["beatmap_scores"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        save_metadata(metadata)
        return fetched

    async def fetch_beatmap_attributes(self, count: int) -> int:
        path = get_fixture_path("beatmap_attributes")
        metadata = load_metadata()
        fetched = 0

        for _ in range(count):
            beatmap_id = random.randint(1, 1000000)
            mods = random.choice([0, 1, 2, 64, 128, 256])
            try:
                data = await self.oac.get_beatmap_attributes(beatmap_id, mods)
                filepath = path / f"beatmap_attrs_{beatmap_id}_mods{mods}.json"
                with open(filepath, "w") as f:
                    json.dump(data, f, indent=2)
                fetched += 1
            except Exception as e:
                self.logger.debug(f"Failed to fetch beatmap attributes {beatmap_id}: {e}")

        metadata["samples"]["beatmap_attributes"]["count"] += fetched
        metadata["samples"]["beatmap_attributes"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        save_metadata(metadata)
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
