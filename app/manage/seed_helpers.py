"""Helper functions for seed command fixture assurance."""
import json
from pathlib import Path

from app.config import PROJECT_ROOT
from app.database.seeding.profiles import SeedProfile
from app.logging import get_logger


async def ensure_fixtures_async(logger, profile: SeedProfile) -> bool:
    """Ensure required fixtures exist by fetching/generating as needed.
    
    Args:
        logger: Logger instance
        profile: Seed profile defining counts
        
    Returns:
        True if fixtures are ready, False otherwise
    """
    fixtures_dir = PROJECT_ROOT / "instance" / "fixtures"
    bms_path = fixtures_dir / "beatmapsets"
    users_path = fixtures_dir / "users"
    
    has_beatmapsets = bms_path.exists() and any(bms_path.glob("beatmapset_*.json"))
    has_users = users_path.exists() and any(users_path.rglob("user_*.json"))
    
    if has_beatmapsets and has_users:
        logger.info("All required fixtures present, skipping fetch.")
        return True
    
    if not has_beatmapsets:
        logger.info(f"Fetching {profile.beatmapsets_count} beatmapsets from osu! API...")
        try:
            from app.redis import RedisClient
            from app.fixtures.orchestrator import FixtureOrchestrator
            from app.fixtures.criteria import FetchCriteria
            
            rc = RedisClient()
            try:
                criteria = FetchCriteria(beatmapsets=profile.beatmapsets_count)
                orchestrator = FixtureOrchestrator(criteria, rc)
                report = await orchestrator.execute()
                fetched = report.results.get("beatmapsets", 0)
                logger.info(f"Fetched {fetched} beatmapset(s).")
                if fetched < profile.beatmapsets_count:
                    logger.warning(
                        f"Expected {profile.beatmapsets_count} beatmapsets, "
                        f"only got {fetched}. Proceeding with what we have."
                    )
            finally:
                await rc.aclose()
        except Exception as e:
            logger.error(f"Failed to fetch beatmapsets: {e}")
            return False
        has_beatmapsets = True
    
    if not has_users:
        logger.info("Fetching beatmapset owner users...")
        try:
            from app.redis import RedisClient
            from app.fixtures.orchestrator import FixtureOrchestrator
            from app.fixtures.criteria import FetchCriteria
            
            # Extract owner user IDs from beatmapset fixtures
            owner_ids: set[int] = set()
            for f in sorted(bms_path.glob("beatmapset_*.json")):
                try:
                    with open(f) as fh:
                        data = json.load(fh)
                    user_id = data.get("user_id")
                    if user_id:
                        owner_ids.add(user_id)
                except (json.JSONDecodeError, KeyError):
                    continue
            
            if not owner_ids:
                logger.error("No owner user IDs found in beatmapset fixtures.")
                return False
            
            user_ids = sorted(owner_ids)
            logger.info(f"Found {len(user_ids)} unique owner(s), fetching...")
            
            rc = RedisClient()
            try:
                criteria = FetchCriteria()
                orchestrator = FixtureOrchestrator(criteria, rc)
                report = await orchestrator.fetch_users_by_ids(user_ids, ruleset="osu")
                fetched_count = report.results.get("users", {}).get("osu", 0)
                logger.info(f"Fetched {fetched_count} user(s).")
            finally:
                await rc.aclose()
        except Exception as e:
            logger.error(f"Failed to fetch users: {e}")
            return False
    
    return True
