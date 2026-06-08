import json
import random
from datetime import datetime, timezone
from typing import AsyncIterator, Optional

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
    load_top_player_ids,
    save_top_player_ids,
)

MAX_RETRIES = 10
RANKING_PAGE_SIZE = 50


class FetchEvent:
    def __init__(self, category: str, current: int, total: int):
        self.category = category
        self.current = current
        self.total = total


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
        self.top_player_ids = self.metadata.get("top_player_ids", {r: [] for r in RULESETS})
        self.last_fetch_results = {}
        self._current_session_results = {}

    async def fetch_beatmaps(self, count: int) -> AsyncIterator[FetchEvent]:
        path = get_fixture_path("beatmaps")
        fetched = 0
        attempts = 0
        max_attempts = count * 10

        while fetched < count and attempts < max_attempts:
            attempts += 1
            beatmap_id = self._get_random_id("beatmaps", avoid_failed=False)
            retries = 0
            while retries < MAX_RETRIES:
                try:
                    data = await self.oac.get_beatmap(beatmap_id)
                    filepath = path / f"beatmap_{beatmap_id}.json"
                    with open(filepath, "w") as f:
                        json.dump(data, f, indent=2)
                    fetched += 1
                    self.logger.debug(f"Fetched beatmap {beatmap_id} ({fetched}/{count})")
                    break
                except Exception as e:
                    self.logger.debug(f"Failed to fetch beatmap {beatmap_id} (retry {retries + 1}/{MAX_RETRIES}): {e}")
                    self._add_failed_id("beatmaps", beatmap_id)
                    retries += 1
                    if retries < MAX_RETRIES:
                        beatmap_id = self._get_random_id("beatmaps", avoid_failed=True)
            
            yield FetchEvent("beatmaps", fetched, count)

        if fetched < count:
            self.logger.warning(f"Only fetched {fetched}/{count} beatmaps")

        self.metadata["samples"]["beatmaps"]["count"] += fetched
        self.metadata["samples"]["beatmaps"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        save_metadata(self.metadata)
        self._current_session_results["beatmaps"] = fetched

    async def fetch_beatmapsets(self, count: int) -> AsyncIterator[FetchEvent]:
        path = get_fixture_path("beatmapsets")
        fetched = 0
        attempts = 0
        max_attempts = count * 10

        while fetched < count and attempts < max_attempts:
            attempts += 1
            beatmapset_id = self._get_random_id("beatmapsets", avoid_failed=False)
            retries = 0
            while retries < MAX_RETRIES:
                try:
                    data = await self.oac.get_beatmapset(beatmapset_id)
                    filepath = path / f"beatmapset_{beatmapset_id}.json"
                    with open(filepath, "w") as f:
                        json.dump(data, f, indent=2)
                    fetched += 1
                    self.logger.debug(f"Fetched beatmapset {beatmapset_id} ({fetched}/{count})")
                    break
                except Exception as e:
                    self.logger.debug(f"Failed to fetch beatmapset {beatmapset_id} (retry {retries + 1}/{MAX_RETRIES}): {e}")
                    self._add_failed_id("beatmapsets", beatmapset_id)
                    retries += 1
                    if retries < MAX_RETRIES:
                        beatmapset_id = self._get_random_id("beatmapsets", avoid_failed=True)
            
            yield FetchEvent("beatmapsets", fetched, count)

        if fetched < count:
            self.logger.warning(f"Only fetched {fetched}/{count} beatmapsets")

        self.metadata["samples"]["beatmapsets"]["count"] += fetched
        self.metadata["samples"]["beatmapsets"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        save_metadata(self.metadata)
        self._current_session_results["beatmapsets"] = fetched

    async def fetch_users(
        self,
        users_osu: int,
        users_taiko: int,
        users_fruits: int,
        users_mania: int,
    ) -> AsyncIterator[FetchEvent]:
        path = get_fixture_path("users")
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

            for i in range(count):
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
                        self.logger.debug(f"Fetched user {user_id} ({ruleset}) ({fetched[ruleset]}/{count})")
                        break
                    except Exception as e:
                        self.logger.debug(f"Failed to fetch user {user_id} ({ruleset}) (retry {retries + 1}/{MAX_RETRIES}): {e}")
                        self._add_failed_id(f"users.{ruleset}", user_id)
                        retries += 1
                        user_id = self._get_random_id(f"users.{ruleset}")
                
                cumulative_count += 1
                yield FetchEvent("users", cumulative_count, total_count)

        self.metadata["samples"]["users"]["count"] += sum(fetched.values())
        self.metadata["samples"]["users"]["per_ruleset"] = {
            r: self.metadata["samples"]["users"]["per_ruleset"].get(r, 0) + fetched[r] for r in RULESETS
        }
        self.metadata["samples"]["users"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        save_metadata(self.metadata)
        self._current_session_results["users"] = fetched.copy()

    async def fetch_scores(
        self,
        scores_best: int,
        scores_firsts: int,
        scores_recent: int,
    ) -> AsyncIterator[FetchEvent]:
        if not self.top_player_ids.get(RULESETS[0]) or all(len(ids) == 0 for ids in self.top_player_ids.values()):
            self.logger.info("Top player IDs not found or empty. Fetching top players first...")
            await self.fetch_top_players()

        path = get_fixture_path("scores")
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

            for i in range(count):
                use_top_players = score_type in ["firsts", "recent"]
                user_id = self._get_random_id("users", use_top_players=use_top_players)
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
                                user_id = self._get_random_id("users", use_top_players=True)
                            else:
                                user_id = self._get_random_id("users", use_top_players=use_top_players)
                            continue
                        filepath = type_path / f"scores_{user_id}_{score_type}.json"
                        with open(filepath, "w") as f:
                            json.dump(data, f, indent=2)
                        fetched[score_type] += 1
                        self.logger.debug(f"Fetched scores for user {user_id} ({score_type}) ({fetched[score_type]}/{count})")
                        break
                    except Exception as e:
                        self.logger.debug(f"Failed to fetch scores for user {user_id} ({score_type}) (retry {retries + 1}/{MAX_RETRIES}): {e}")
                        self._add_failed_id("users", user_id)
                        retries += 1
                        if retries >= MAX_RETRIES and score_type == "best":
                            user_id = self._get_random_id("users", use_top_players=True)
                        else:
                            user_id = self._get_random_id("users", use_top_players=use_top_players)
                
                cumulative_count += 1
                yield FetchEvent("scores", cumulative_count, total_count)

        self.metadata["samples"]["scores"]["count"] += sum(fetched.values())
        self.metadata["samples"]["scores"]["per_type"] = {
            t: self.metadata["samples"]["scores"]["per_type"].get(t, 0) + fetched[t] for t in SCORE_TYPES
        }
        self.metadata["samples"]["scores"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        save_metadata(self.metadata)
        self._current_session_results["scores"] = fetched.copy()

    async def fetch_beatmap_scores(self, count: int) -> AsyncIterator[FetchEvent]:
        path = get_fixture_path("beatmap_scores")
        fetched = 0

        for i in range(count):
            beatmap_id = self._get_random_id("beatmaps")
            retries = 0
            while retries < MAX_RETRIES:
                try:
                    data = await self.oac.get_beatmap_scores(beatmap_id, limit=1)
                    scores = data.get("scores", [])
                    if not scores:
                        self.logger.debug(f"Empty scores for beatmap {beatmap_id} (retry {retries + 1}/{MAX_RETRIES})")
                        retries += 1
                        beatmap_id = self._get_random_id("beatmaps")
                        continue
                    filepath = path / f"beatmap_scores_{beatmap_id}.json"
                    with open(filepath, "w") as f:
                        json.dump(data, f, indent=2)
                    fetched += 1
                    self.logger.debug(f"Fetched beatmap scores {beatmap_id} ({fetched}/{count})")
                    break
                except Exception as e:
                    self.logger.debug(f"Failed to fetch beatmap scores {beatmap_id} (retry {retries + 1}/{MAX_RETRIES}): {e}")
                    self._add_failed_id("beatmaps", beatmap_id)
                    retries += 1
                    beatmap_id = self._get_random_id("beatmaps")
            
            yield FetchEvent("beatmap_scores", i + 1, count)

        self.metadata["samples"]["beatmap_scores"]["count"] += fetched
        self.metadata["samples"]["beatmap_scores"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        save_metadata(self.metadata)
        self._current_session_results["beatmap_scores"] = fetched

    async def fetch_beatmap_attributes(self, count: int) -> AsyncIterator[FetchEvent]:
        path = get_fixture_path("beatmap_attributes")
        fetched = 0

        for i in range(count):
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
                    self.logger.debug(f"Fetched beatmap attributes {beatmap_id} ({fetched}/{count})")
                    break
                except Exception as e:
                    self.logger.debug(f"Failed to fetch beatmap attributes {beatmap_id} (retry {retries + 1}/{MAX_RETRIES}): {e}")
                    self._add_failed_id("beatmaps", beatmap_id)
                    retries += 1
                    beatmap_id = self._get_random_id("beatmaps")
            
            yield FetchEvent("beatmap_attributes", i + 1, count)

        self.metadata["samples"]["beatmap_attributes"]["count"] += fetched
        self.metadata["samples"]["beatmap_attributes"]["last_fetched"] = datetime.now(timezone.utc).isoformat()
        save_metadata(self.metadata)
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
            async for event in self.fetch_beatmaps(beatmaps_count):
                yield event
        
        if beatmapsets_count > 0:
            async for event in self.fetch_beatmapsets(beatmapsets_count):
                yield event
        
        if users_osu > 0 or users_taiko > 0 or users_fruits > 0 or users_mania > 0:
            async for event in self.fetch_users(users_osu, users_taiko, users_fruits, users_mania):
                yield event
        
        if scores_best > 0 or scores_firsts > 0 or scores_recent > 0:
            async for event in self.fetch_scores(scores_best, scores_firsts, scores_recent):
                yield event
        
        if beatmap_scores_count > 0:
            async for event in self.fetch_beatmap_scores(beatmap_scores_count):
                yield event
        
        if beatmap_attributes_count > 0:
            async for event in self.fetch_beatmap_attributes(beatmap_attributes_count):
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
                    self.logger.error(f"Error fetching ranking for {ruleset_name}: {e}")
                    break
            
            fetched[ruleset_name] = player_ids[:count_per_ruleset]
            self.logger.info(f"Fetched {len(player_ids)} top players for {ruleset_name}")
        
        current_top_ids = load_top_player_ids()
        current_top_ids.update(fetched)
        save_top_player_ids(current_top_ids)
        self.metadata = load_metadata()
        self.top_player_ids = self.metadata.get("top_player_ids", {r: [] for r in RULESETS})
        return fetched

    def _get_random_id(self, category: str, use_top_players: bool = False, avoid_failed: bool = True) -> int:
        if use_top_players and category == "users" and self.top_player_ids:
            for ruleset in RULESETS:
                top_ids = self.top_player_ids.get(ruleset, [])
                if top_ids:
                    if avoid_failed:
                        failed_list = self.failed_ids.get("users", {}).get(ruleset, [])
                        for candidate in top_ids:
                            if candidate not in failed_list:
                                return candidate
                    else:
                        return random.choice(top_ids)
        
        range_config = self.id_ranges.get(category, self.id_ranges.get(category.split(".")[0], {"min": 1, "max": 1000000}))
        min_id = range_config.get("min", 1)
        max_id = range_config.get("max", 1000000)
        
        failed_list = self.failed_ids.get(category, [])
        
        if avoid_failed:
            for _ in range(MAX_RETRIES * 3):
                candidate = random.randint(min_id, max_id)
                if candidate not in failed_list:
                    return candidate
        
        return random.randint(min_id, max_id)

    def _add_failed_id(self, category: str, id_: int) -> None:
        if category not in self.failed_ids:
            self.failed_ids[category] = []
        
        category_ids = self.failed_ids[category]
        
        if isinstance(category_ids, dict):
            for subcategory in category_ids.values():
                if id_ not in subcategory:
                    subcategory.append(id_)
                    if len(subcategory) > 1000:
                        subcategory[:] = subcategory[-1000:]
        else:
            if id_ not in category_ids:
                category_ids.append(id_)
                if len(category_ids) > 1000:
                    category_ids[:] = category_ids[-1000:]
