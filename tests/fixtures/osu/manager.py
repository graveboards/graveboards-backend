from pathlib import Path
from typing import Optional
import json
import random

from app.logging import get_logger
from app.config import PROJECT_ROOT

logger = get_logger(__name__)

RULESETS = ["osu", "taiko", "fruits", "mania"]
SCORE_TYPES = ["best", "firsts", "recent"]
DISCUSSION_STATUSES = ["ranked", "loved", "qualified", "graveyard", "pending", "approved", "all"]


def load_metadata() -> dict:
    """Load metadata from default location."""
    metadata_path = PROJECT_ROOT / "instance" / "fixtures" / "metadata.json"
    if metadata_path.exists():
        try:
            with open(metadata_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_metadata(metadata: dict) -> None:
    """Save metadata to default location."""
    metadata_path = PROJECT_ROOT / "instance" / "fixtures" / "metadata.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)


def get_fixture_path(category: str, subcategory: str | None = None) -> Path:
    """Get fixture path for a category."""
    path = PROJECT_ROOT / "tests" / "fixtures" / "osu" / category
    if subcategory:
        path = path / subcategory
    path.mkdir(parents=True, exist_ok=True)
    return path


class FixtureManager:
    """Fixture abstraction layer that decouples tests from raw fixture files."""
    
    def __init__(self, fixture_dir: Path = None, metadata: dict = None):
        self.fixture_dir = fixture_dir or PROJECT_ROOT / "tests" / "fixtures" / "osu"
        self.metadata = metadata or load_metadata()
        self._init_metadata()
    
    def _init_metadata(self):
        """Initialize metadata structure for targeted fixtures."""
        if "targeted" not in self.metadata:
            self.metadata["targeted"] = {
                "beatmaps": {
                    "by_status": {},
                    "by_ruleset": {},
                    "by_difficulty": {},
                    "by_playcount": {},
                    "file_metadata": {},
                },
                "beatmapsets": {
                    "by_status": {},
                    "file_metadata": {},
                },
                "users": {
                    "by_activity": {},
                    "per_ruleset": {},
                    "file_metadata": {},
                },
                "scores": {
                    "by_rank": {},
                    "by_mods": {},
                    "file_metadata": {},
                },
            }
    
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
            if self._matches_preferences(meta, preferences):
                filepath = meta.get("filepath")
                if filepath:
                    file_paths.append(Path(filepath))
        
        return file_paths
    
    def _matches_preferences(
        self,
        metadata: dict,
        preferences: dict,
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
        """Check if difficulty is in allowed range."""
        ranges = {
            "easy": (0, 2.0),
            "medium": (2.0, 5.0),
            "hard": (5.0, 7.0),
            "expert": (7.0, 999.0),
        }
        if difficulty_range not in ranges:
            return True
        min_diff, max_diff = ranges[difficulty_range]
        return min_diff <= difficulty <= max_diff
    
    def _in_playcount_range(
        self,
        playcount: int,
        playcount_range: str,
    ) -> bool:
        """Check if playcount is in allowed range."""
        ranges = {
            "low": (0, 100),
            "medium": (100, 1000),
            "high": (1000, 999999999),
        }
        if playcount_range not in ranges:
            return True
        min_pc, max_pc = ranges[playcount_range]
        return min_pc <= playcount <= max_pc
    
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
        
        return None
    
    def get_coverage_report(self) -> dict:
        """Get current fixture coverage."""
        targeted_metadata = self.metadata.get("targeted", {})
        return targeted_metadata
    
    def ensure_coverage(
        self,
        targets: dict,
    ) -> dict:
        """Ensure minimum coverage, fetch if needed."""
        coverage = self.get_coverage_report()
        gaps = {}
        
        for category, category_targets in targets.items():
            if category not in coverage:
                gaps[category] = category_targets
                continue
            
            category_coverage = coverage[category]
            
            if "by_status" in category_targets:
                for status, min_count in category_targets["by_status"].items():
                    actual_count = category_coverage.get("by_status", {}).get(status, 0)
                    if actual_count < min_count:
                        if category not in gaps:
                            gaps[category] = {}
                        if "by_status" not in gaps[category]:
                            gaps[category]["by_status"] = {}
                        gaps[category]["by_status"][status] = min_count - actual_count
            
            if "by_ruleset" in category_targets:
                for ruleset, min_count in category_targets["by_ruleset"].items():
                    actual_count = category_coverage.get("by_ruleset", {}).get(ruleset, 0)
                    if actual_count < min_count:
                        if category not in gaps:
                            gaps[category] = {}
                        if "by_ruleset" not in gaps[category]:
                            gaps[category]["by_ruleset"] = {}
                        gaps[category]["by_ruleset"][ruleset] = min_count - actual_count
        
        return gaps
