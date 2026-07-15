from pathlib import Path
from typing import Optional
import json
import random

from app.logging import get_logger
from app.config import PROJECT_ROOT

from .metadata_io import load_metadata, save_metadata, create_targeted_metadata
from .paths import get_fixture_path
from .constants import RULESETS, SCORE_TYPES
from .metadata import FixtureMetadataManager

logger = get_logger(__name__)


class FixtureReader:
    """Fixture abstraction layer that decouples tests from raw fixture files."""
    
    def __init__(self, fixture_dir: Path = None, metadata: dict = None):
        self.fixture_dir = fixture_dir or PROJECT_ROOT / "tests" / "fixtures" / "osu"
        self.metadata = metadata or load_metadata()
        self.metadata_manager = FixtureMetadataManager(self.metadata, self.fixture_dir)
        self.metadata_manager.init_metadata()
    
    def get_beatmap_by_id(self, beatmap_id: int) -> Optional[dict]:
        """Get a specific beatmap by ID."""
        return self._get_fixture_by_id("beatmaps", beatmap_id)
    
    def get_beatmapset_by_id(self, beatmapset_id: int) -> Optional[dict]:
        """Get a specific beatmapset by ID."""
        return self._get_fixture_by_id("beatmapsets", beatmapset_id)
    
    def get_user_by_id(self, user_id: int, ruleset: str) -> Optional[dict]:
        """Get a specific user by ID."""
        return self._get_fixture_by_id(f"users.{ruleset}", user_id, prefix=f"user_{user_id}_{ruleset}")
    
    def get_beatmap_scores_by_beatmap(self, beatmap_id: int) -> Optional[dict]:
        """Get beatmap scores by beatmap ID."""
        return self._get_fixture_by_id("beatmap_scores", beatmap_id, prefix=f"scores_{beatmap_id}")
    
    def get_beatmap_attributes_by_beatmap(self, beatmap_id: int) -> Optional[dict]:
        """Get beatmap attributes by beatmap ID."""
        return self._get_fixture_by_id("beatmap_attributes", beatmap_id, prefix=f"beatmap_attrs_{beatmap_id}")
    
    # High-level fixture requests
    def get_beatmaps(
        self,
        count: int = 1,
        by_status: list[str] = None,
        by_ruleset: str = None,
        by_difficulty: str = None,
        by_playcount: str = None,
    ) -> list[dict]:
        """Get beatmap fixtures by preference."""
        preferences = {
            "by_status": by_status,
            "by_ruleset": by_ruleset,
            "by_difficulty": by_difficulty,
            "by_playcount": by_playcount,
        }
        return self._get_fixtures("beatmaps", count, preferences)
    
    def get_beatmapsets(
        self,
        count: int = 1,
        by_status: list[str] = None,
    ) -> list[dict]:
        """Get beatmapset fixtures by preference."""
        preferences = {"by_status": by_status}
        return self._get_fixtures("beatmapsets", count, preferences)
    
    def get_users(
        self,
        ruleset: str,
        count: int = 1,
        activity_level: str = None,
    ) -> list[dict]:
        """Get user fixtures by preference."""
        preferences = {"activity_level": activity_level}
        return self._get_fixtures(f"users.{ruleset}", count, preferences)
    
    def get_scores(
        self,
        score_type: str,
        count: int = 1,
        rank_coverage: list[str] = None,
        mod_coverage: list[str] = None,
    ) -> list[dict]:
        """Get score fixtures by preference."""
        preferences = {
            "rank_coverage": rank_coverage,
            "mod_coverage": mod_coverage,
        }
        return self._get_fixtures(f"scores.{score_type}", count, preferences)
    
    def get_beatmap_scores(
        self,
        beatmap_id: int = None,
        count: int = 1,
    ) -> list[dict]:
        """Get beatmap score fixtures."""
        preferences = {"beatmap_id": beatmap_id}
        return self._get_fixtures("beatmap_scores", count, preferences)
    
    def get_beatmap_attributes(
        self,
        beatmap_id: int = None,
        mods: list[int] = None,
    ) -> dict:
        """Get beatmap attribute fixtures."""
        preferences = {"beatmap_id": beatmap_id, "mods": mods}
        fixtures = self._get_fixtures("beatmap_attributes", 1, preferences)
        return fixtures[0] if fixtures else None
    
    def get_queue_by_id(self, queue_id: int) -> Optional[dict]:
        """Get a specific queue by ID."""
        return self._get_fixture_by_id("queues", queue_id)
    
    def get_request_by_id(self, request_id: int) -> Optional[dict]:
        """Get a specific request by ID."""
        return self._get_fixture_by_id("requests", request_id)
    
    def get_queues(
        self,
        count: int = 1,
        by_visibility: int = None,
        by_is_open: bool = None,
    ) -> list[dict]:
        """Get queue fixtures by preference."""
        preferences = {"by_visibility": by_visibility, "by_is_open": by_is_open}
        return self._get_fixtures("queues", count, preferences)
    
    def get_requests(
        self,
        count: int = 1,
        by_status: int = None,
        by_mv_checked: bool = None,
    ) -> list[dict]:
        """Get request fixtures by preference."""
        preferences = {"by_status": by_status, "by_mv_checked": by_mv_checked}
        return self._get_fixtures("requests", count, preferences)
    
    def _get_fixtures(
        self,
        category: str,
        count: int,
        preferences: dict,
    ) -> list[dict]:
        """Resolve preferences to fixture files and load them."""
        fixture_files = self._resolve_preference(category, preferences)
        
        if count > len(fixture_files):
            logger.warning(
                f"Requested {count} fixtures but only {len(fixture_files)} available "
                f"for {category}. Returning all available."
            )
        
        fixtures = []
        for file_path in fixture_files[:count]:
            fixture = self._load_fixture(category, file_path)
            if fixture:
                fixtures.append(fixture)
        
        return fixtures
    
    def _resolve_preference(
        self,
        category: str,
        preferences: dict,
    ) -> list[Path]:
        """Resolve preferences to list of fixture file paths."""
        targeted_metadata = self.metadata.get("targeted", {})
        
        # Handle subcategories (e.g., "users.osu" -> "users")
        parts = category.split(".")
        if len(parts) > 1:
            main_category = parts[0]
            category_metadata = targeted_metadata.get(main_category, {})
        else:
            main_category = category
            category_metadata = targeted_metadata.get(category, {})
        
        file_metadata = category_metadata.get("file_metadata", {})
        
        available_files = []
        
        if not file_metadata:
            available_files = list(self._get_fixture_files(category))
            for file_path in available_files:
                fixture_id = self._extract_id_from_path(file_path, category)
                if fixture_id:
                    file_metadata[str(fixture_id)] = {
                        "filepath": str(file_path),
                        "loaded": False,
                    }
            if main_category in targeted_metadata:
                targeted_metadata[main_category]["file_metadata"] = file_metadata
        
        file_paths = []
        for fixture_id, meta in file_metadata.items():
            if self._matches_preferences(meta, preferences, category=category):
                filepath = meta.get("filepath")
                if filepath:
                    file_paths.append(Path(filepath))
        
        return file_paths
    
    def _matches_preferences(
        self,
        metadata: dict,
        preferences: dict,
        category: str = "",
    ) -> bool:
        """Check if fixture metadata matches preferences."""
        for pref_key, pref_value in preferences.items():
            if pref_value is None:
                continue
            
            if pref_key == "by_status":
                fixture_status = metadata.get("status")
                if not self._in_list(fixture_status, pref_value):
                    return False
            
            elif pref_key == "by_ruleset":
                fixture_ruleset = metadata.get("ruleset")
                if fixture_ruleset and fixture_ruleset != pref_value:
                    return False
            
            elif pref_key == "by_difficulty":
                fixture_diff = metadata.get("difficulty_rating")
                if fixture_diff is not None:
                    if not self._in_difficulty_range(fixture_diff, pref_value):
                        return False
            
            elif pref_key == "by_playcount":
                fixture_playcount = metadata.get("playcount")
                if fixture_playcount is not None:
                    if not self._in_playcount_range(fixture_playcount, pref_value):
                        return False
            
            elif pref_key == "activity_level":
                fixture_activity = metadata.get("activity_level")
                if fixture_activity != pref_value:
                    return False
            
            elif pref_key == "rank_coverage":
                fixture_rank = metadata.get("rank")
                if not self._in_list(fixture_rank, pref_value):
                    return False
            
            elif pref_key == "mod_coverage":
                fixture_mods = metadata.get("mods", [])
                if not any(mod in pref_value for mod in fixture_mods):
                    return False
            
            elif pref_key == "beatmap_id":
                fixture_beatmap_id = metadata.get("beatmap_id")
                if fixture_beatmap_id != pref_value:
                    return False
            
            elif pref_key == "mods":
                fixture_mods = metadata.get("mods", [])
                if set(pref_value) != set(fixture_mods):
                    return False
            
            elif pref_key == "by_visibility":
                fixture_visibility = metadata.get("visibility")
                if fixture_visibility is not None and fixture_visibility != pref_value:
                    return False
            
            elif pref_key == "by_is_open":
                fixture_is_open = metadata.get("is_open")
                if fixture_is_open is not None and fixture_is_open != pref_value:
                    return False
            
            elif pref_key == "by_status":
                if category == "requests":
                    fixture_status = metadata.get("status")
                    if fixture_status is not None and fixture_status != pref_value:
                        return False
            
            elif pref_key == "by_mv_checked":
                fixture_mv_checked = metadata.get("mv_checked")
                if fixture_mv_checked is not None and fixture_mv_checked != pref_value:
                    return False
        
        return True
    
    def _in_list(
        self,
        value: any,
        allowed_values: list,
    ) -> bool:
        """Check if value is in list of allowed values."""
        if value is None:
            return True
        return value in allowed_values
    
    def _in_difficulty_range(
        self,
        difficulty: float,
        difficulty_range: str,
    ) -> bool:
        """Check if difficulty is in allowed range using half-open intervals."""
        ranges = {
            "easy": (0, 2.0),
            "medium": (2.0, 5.0),
            "hard": (5.0, 7.0),
            "expert": (7.0, 999.0),
        }
        if difficulty_range not in ranges:
            return True
        min_diff, max_diff = ranges[difficulty_range]
        return min_diff <= difficulty < max_diff
    
    def _in_playcount_range(
        self,
        playcount: int,
        playcount_range: str,
    ) -> bool:
        """Check if playcount is in allowed range using half-open intervals."""
        ranges = {
            "low": (0, 100),
            "medium": (100, 1000),
            "high": (1000, 999999999),
        }
        if playcount_range not in ranges:
            return True
        min_pc, max_pc = ranges[playcount_range]
        return min_pc <= playcount < max_pc
    
    def _get_fixture_by_id(
        self,
        category: str,
        fixture_id: int,
        prefix: str = None,
    ) -> Optional[dict]:
        """Get a specific fixture by ID."""
        file_metadata = self.metadata.get("targeted", {}).get(category, {}).get("file_metadata", {})
        
        if str(fixture_id) in file_metadata:
            filepath = file_metadata[str(fixture_id)].get("filepath")
            if filepath:
                return self._load_fixture(category, Path(filepath))
        
        if prefix:
            path = self.fixture_dir / Path(*category.split("."))
            if path.exists():
                file_path = path / f"{prefix}.json"
                if file_path.exists():
                    return self._load_fixture(category, file_path)
        
        return None
    
    def _load_fixture(
        self,
        category: str,
        file_path: Path,
    ) -> Optional[dict]:
        """Load fixture from file."""
        try:
            with open(file_path) as f:
                data = json.load(f)
            return data
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Failed to load fixture {file_path}: {e}")
            return None
    
    def _get_fixture_files(
        self,
        category: str,
    ) -> list[Path]:
        """Get all fixture files for a category."""
        parts = category.split(".")
        path = self.fixture_dir / Path(*parts)
        if not path.exists():
            return []
        return list(path.glob("*.json"))
    
    def _extract_id_from_path(
        self,
        file_path: Path,
        category: str,
    ) -> Optional[int]:
        """Extract fixture ID from filename."""
        filename = file_path.stem
        
        if category == "beatmaps":
            if filename.startswith("beatmap_"):
                return int(filename[8:])
        
        elif category == "beatmapsets":
            if filename.startswith("beatmapset_"):
                return int(filename[11:])
        
        elif category.startswith("users."):
            if filename.startswith("user_"):
                parts = filename.split("_")
                if len(parts) >= 2:
                    return int(parts[1])
        
        elif category.startswith("scores."):
            if filename.startswith("scores_"):
                parts = filename.split("_")
                if len(parts) >= 2:
                    return int(parts[1])
        
        elif category == "beatmap_scores":
            if filename.startswith("beatmap_scores_"):
                return int(filename[15:])
        
        elif category == "beatmap_attributes":
            if filename.startswith("beatmap_attrs_"):
                parts = filename.split("_")
                if len(parts) >= 2:
                    return int(parts[2])
        
        elif category == "queues":
            if filename.startswith("queue_"):
                return int(filename[6:])
        
        elif category == "requests":
            if filename.startswith("request_"):
                return int(filename[8:])
        
        return None
    
    async def refresh_category_metadata(
        self,
        category: str,
        dry_run: bool = False
    ) -> list[dict]:
        """Refresh metadata for a category to match disk state."""
        return await self.metadata_manager.refresh_category_metadata(category, dry_run)
    
    def get_coverage_report(self) -> dict:
        """Get current fixture coverage."""
        return self.metadata_manager.get_coverage_report()
    
    def ensure_coverage(
        self,
        targets: dict,
    ) -> dict:
        """Ensure minimum coverage, fetch if needed."""
        return self.metadata_manager.ensure_coverage(targets)
