"""Metadata management for fixture coverage tracking."""

from pathlib import Path
from app.logging import get_logger
from .utils import save_metadata

logger = get_logger(__name__)


class FixtureMetadataManager:
    """Handles metadata operations for fixture coverage tracking."""
    
    def __init__(self, metadata: dict, fixture_dir: Path):
        self.metadata = metadata
        self.fixture_dir = fixture_dir
    
    def init_metadata(self):
        """Initialize metadata structure for targeted fixtures."""
        from .utils import create_targeted_metadata
        if "targeted" not in self.metadata:
            self.metadata["targeted"] = create_targeted_metadata()
    
    @staticmethod
    def _get_current_timestamp() -> str:
        """Get current UTC timestamp in ISO format."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
    
    async def refresh_category_metadata(
        self,
        category: str,
        dry_run: bool = False
    ) -> list[dict]:
        """Refresh metadata for a category to match disk state.
        
        Args:
            category: Category to refresh
            dry_run: If True, only return changes without applying
            
        Returns:
            List of change records
        """
        from .utils import RULESETS, SCORE_TYPES
        
        changes = []
        metadata = self.metadata.get("promoted_fixtures", {})
        current_meta = metadata.get(category, {})
        
        # Count files on disk
        category_path = self.fixture_dir / category
        disk_files = []
        
        if category_path.exists():
            disk_files = [f.name for f in category_path.glob("*.json")]
        
        disk_count = len(disk_files)
        
        # Check if ruleset subcategories exist
        if category == "users":
            for ruleset in RULESETS:
                ruleset_path = category_path / ruleset
                if ruleset_path.exists():
                    ruleset_files = [f.name for f in ruleset_path.glob("*.json")]
                    if ruleset_files:
                        disk_count += len(ruleset_files)
        
        # Check if score type subcategories exist
        elif category == "scores":
            for score_type in SCORE_TYPES:
                score_path = category_path / score_type
                if score_path.exists():
                    score_files = [f.name for f in score_path.glob("*.json")]
                    if score_files:
                        disk_count += len(score_files)
        
        # Compare with metadata
        old_meta_count = current_meta.get("count", 0)
        
        if old_meta_count != disk_count:
            change = {
                "category": category,
                "action": "sync" if disk_count > 0 else "remove" if old_meta_count > 0 and disk_count == 0 else "add",
                "fixture_id": category,
                "disk_count": disk_count,
                "old_meta_count": old_meta_count
            }
            
            if not dry_run:
                if disk_count > 0:
                    metadata[category] = {
                        "count": disk_count,
                        "last_refreshed": self._get_current_timestamp()
                    }
                elif old_meta_count > 0:
                    del metadata[category]
                self.metadata["promoted_fixtures"] = metadata
                save_metadata(self.metadata)
            
            changes.append(change)
        
        return changes
    
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
