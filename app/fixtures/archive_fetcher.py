"""Archive-based fixture fetcher using osu.sh data source.

This module provides an alternative fixture fetcher that uses osu.sh
archives to get reliable user IDs, then fetches the actual fixture data
from the osu API. This replaces the "guess and hope" strategy with a
more efficient approach.

Key features:
- Uses SQL dumps from osu.sh archives to extract working player IDs
- Falls back to osu! API for real-time data
- Maintains backward compatibility with existing fetcher
"""
import json
from pathlib import Path
from typing import Optional

from app.redis import RedisClient
from app.osu_api.client.osu_api_client import OsuAPIClient
from app.osu_api.enums import Ruleset, ScoreType

from .archives import (
    load_archive_index,
    refresh_archive_index,
    get_user_ids_from_archive,
    get_beatmap_ids_from_archive,
    ArchiveInfo,
    ARCHIVE_DIR,
)
from .fetcher import FixtureDataFetcher
from .utils import (
    load_metadata,
    save_metadata,
    get_fixture_path,
    RULESETS,
    TOP_PLAYERS_PER_RULESET,
    load_top_player_ids,
    save_top_player_ids,
)


class ArchiveBasedFixtureFetcher(FixtureDataFetcher):
    """Fixture fetcher that uses osu.sh archives as primary data source.
    
    This fetcher leverages the structured SQL dumps from osu.sh archives
    to obtain reliable user IDs, then fetches the actual fixture data
    from the osu API. This is much more efficient than random ID guessing.
    """
    
    def __init__(self, rc: RedisClient, id_ranges: dict | None = None, use_archives: bool = True):
        super().__init__(rc, id_ranges)
        self.use_archives = use_archives
        self.archive_player_ids = {r: [] for r in RULESETS}
        self.archive_beatmap_ids = []
    
    async def refresh_archive_data(self) -> None:
        """Refresh archive data and extract IDs."""
        if not self.use_archives:
            return
        
        logger = self.logger
        
        try:
            archive_index = await refresh_archive_index()
        except Exception as e:
            if logger:
                logger.warning(f"Failed to refresh archive index: {e}")
            return
        
        # Extract player IDs from latest archives
        for ruleset in RULESETS:
            top_archive = archive_index.get_latest_archive(
                archive_type="performance",
                ruleset=ruleset,
                selection="top",
            )
            
            if top_archive:
                if logger:
                    logger.info(f"Extracting top player IDs from {top_archive.filename}")
                
                ids = get_user_ids_from_archive(top_archive, min_playcount=50)
                
                if ids:
                    # Store as top player IDs
                    self.archive_player_ids[ruleset] = ids[:TOP_PLAYERS_PER_RULESET]
                    
                    # Also save to metadata
                    current_ids = load_top_player_ids()
                    current_ids[ruleset] = self.archive_player_ids[ruleset]
                    save_top_player_ids(current_ids)
        
        # Extract beatmap IDs from latest osu_files archive
        osu_files_archive = archive_index.get_latest_archive(
            archive_type="osu_files",
        )
        
        if osu_files_archive:
            if logger:
                logger.info(f"Extracting beatmap IDs from {osu_files_archive.filename}")
            
            self.archive_beatmap_ids = get_beatmap_ids_from_archive(osu_files_archive)
    
    def _get_player_ids_for_ruleset(self, ruleset: str, prefer_archived: bool = True) -> list[int]:
        """Get player IDs for a ruleset, preferring archived IDs."""
        if prefer_archived and self.archive_player_ids.get(ruleset):
            return self.archive_player_ids[ruleset]
        
        # Fallback to top player IDs from metadata
        metadata = load_metadata()
        return metadata.get("top_player_ids", {}).get(ruleset, [])
    
    def _get_beatmap_ids(self, prefer_archived: bool = True) -> list[int]:
        """Get beatmap IDs, preferring archived IDs."""
        if prefer_archived and self.archive_beatmap_ids:
            return self.archive_beatmap_ids
        
        # Fallback to random IDs from ID ranges
        range_config = self.id_ranges.get("beatmaps", {"min": 1, "max": 1000000})
        return list(range(range_config["min"], range_config["max"]))
    
    def _get_random_id(self, category: str, use_top_players: bool = False, avoid_failed: bool = True) -> int:
        """Override to use archived IDs when available."""
        if category == "users" and use_top_players:
            for ruleset in RULESETS:
                archived_ids = self.archive_player_ids.get(ruleset, [])
                if archived_ids:
                    if avoid_failed:
                        failed_list = self.failed_ids.get("users", {}).get(ruleset, [])
                        for candidate in archived_ids:
                            if candidate not in failed_list:
                                return candidate
                    else:
                        import random
                        return random.choice(archived_ids)
        
        if category == "beatmaps" and self.archive_beatmap_ids:
            import random
            if avoid_failed:
                failed_list = self.failed_ids.get("beatmaps", [])
                for candidate in self.archive_beatmap_ids:
                    if candidate not in failed_list:
                        return candidate
            else:
                return random.choice(self.archive_beatmap_ids)
        
        # Fallback to parent implementation (random ID guessing)
        return super()._get_random_id(category, use_top_players, avoid_failed)
    
    async def fetch_top_players(
        self,
        rulesets: Optional[list[str]] = None,
        count_per_ruleset: int = 1000,
        prefer_archives: bool = True,
    ) -> dict[str, list[int]]:
        """Fetch top players, using archives as primary source."""
        if rulesets is None:
            rulesets = RULESETS
        
        if not self.use_archives:
            return await super().fetch_top_players(rulesets, count_per_ruleset)
        
        fetched = {}
        
        if prefer_archives:
            for ruleset_name in rulesets:
                archived_ids = self.archive_player_ids.get(ruleset_name, [])
                
                if archived_ids:
                    ids = archived_ids[:count_per_ruleset]
                    fetched[ruleset_name] = ids
                    if self.logger:
                        self.logger.info(f"Using {len(ids)} archived top players for {ruleset_name}")
                else:
                    # Fall back to API
                    ids = await super().fetch_top_players(
                        rulesets=[ruleset_name],
                        count_per_ruleset=count_per_ruleset
                    )
                    fetched[ruleset_name] = ids[ruleset_name]
        
        else:
            # Use API only
            fetched = await super().fetch_top_players(rulesets, count_per_ruleset)
        
        # Update metadata
        current_ids = load_top_player_ids()
        current_ids.update(fetched)
        save_top_player_ids(current_ids)
        self.top_player_ids = current_ids
        
        return fetched
    
    async def fetch_users(
        self,
        users_osu: int,
        users_taiko: int,
        users_fruits: int,
        users_mania: int,
        prefer_archives: bool = True,
    ) -> None:
        """Fetch users using archived IDs as primary source."""
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
        
        if prefer_archives and self.use_archives:
            for ruleset in RULESETS:
                ruleset_path = path / ruleset
                ruleset_path.mkdir(parents=True, exist_ok=True)
                count = ruleset_counts[ruleset]
                
                archived_ids = self.archive_player_ids.get(ruleset, [])
                
                if archived_ids:
                    # Use archived IDs first
                    for i, user_id in enumerate(archived_ids[:count]):
                        if i >= count:
                            break
                        
                        mode = getattr(Ruleset, ruleset.upper()).value
                        retries = 0
                        while retries < 5:
                            try:
                                data = await self.oac.get_user(user_id, Ruleset(mode))
                                filepath = ruleset_path / f"user_{user_id}_{ruleset}.json"
                                with open(filepath, "w") as f:
                                    json.dump(data, f, indent=2)
                                fetched[ruleset] += 1
                                self.logger.debug(f"Fetched user {user_id} ({ruleset}) ({fetched[ruleset]}/{count})")
                                break
                            except Exception as e:
                                self.logger.debug(f"Failed to fetch user {user_id} ({ruleset}): {e}")
                                retries += 1
                
                # Fill remaining from metadata top players
                if fetched[ruleset] < count:
                    metadata_ids = self._get_player_ids_for_ruleset(ruleset, prefer_archived=False)
                    for user_id in metadata_ids:
                        if fetched[ruleset] >= count:
                            break
                        
                        mode = getattr(Ruleset, ruleset.upper()).value
                        retries = 0
                        while retries < 5:
                            try:
                                data = await self.oac.get_user(user_id, Ruleset(mode))
                                filepath = ruleset_path / f"user_{user_id}_{ruleset}.json"
                                with open(filepath, "w") as f:
                                    json.dump(data, f, indent=2)
                                fetched[ruleset] += 1
                                self.logger.debug(f"Fetched user {user_id} ({ruleset}) from metadata ({fetched[ruleset]}/{count})")
                                break
                            except Exception as e:
                                self.logger.debug(f"Failed to fetch user {user_id} ({ruleset}): {e}")
                                retries += 1
                
                # Final fallback: random guessing
                remaining = count - fetched[ruleset]
                if remaining > 0:
                    self.logger.info(f"Falling back to random guessing for {remaining} {ruleset} users")
                    for _ in range(remaining):
                        user_id = self._get_random_id(f"users.{ruleset}", avoid_failed=True)
                        mode = getattr(Ruleset, ruleset.upper()).value
                        retries = 0
                        while retries < 5:
                            try:
                                data = await self.oac.get_user(user_id, Ruleset(mode))
                                filepath = ruleset_path / f"user_{user_id}_{ruleset}.json"
                                with open(filepath, "w") as f:
                                    json.dump(data, f, indent=2)
                                fetched[ruleset] += 1
                                self.logger.debug(f"Fetched user {user_id} ({ruleset}) random ({fetched[ruleset]}/{count})")
                                break
                            except Exception as e:
                                self.logger.debug(f"Failed to fetch user {user_id} ({ruleset}) random: {e}")
                                retries += 1
        
        else:
            # Use base implementation without archives
            await super().fetch_users(users_osu, users_taiko, users_fruits, users_mania)
            fetched = self._current_session_results.get("users", {}).copy()
        
        self.metadata["samples"]["users"]["count"] += sum(fetched.values())
        self.metadata["samples"]["users"]["per_ruleset"] = {
            r: self.metadata["samples"]["users"]["per_ruleset"].get(r, 0) + fetched[r] for r in RULESETS
        }
        self.metadata["samples"]["users"]["last_fetched"] = self._get_timestamp()
        save_metadata(self.metadata)
        self._current_session_results["users"] = fetched.copy()
    
    async def fetch_scores(
        self,
        scores_best: int,
        scores_firsts: int,
        scores_recent: int,
        prefer_archives: bool = True,
    ) -> None:
        """Fetch scores using archived player IDs as primary source."""
        if prefer_archives and self.use_archives and not self.archive_player_ids.get(RULESETS[0]):
            self.logger.info("Archived player IDs not loaded. Refreshing archive data...")
            await self.refresh_archive_data()
        
        # Ensure we have top players
        if not self.top_player_ids.get(RULESETS[0]) or all(len(ids) == 0 for ids in self.top_player_ids.values()):
            self.logger.info("Top player IDs not found or empty. Fetching from archives...")
            await self.fetch_top_players(prefer_archives=prefer_archives)
        
        # Use base implementation but with updated player IDs
        await super().fetch_scores(scores_best, scores_firsts, scores_recent)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
