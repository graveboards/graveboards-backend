"""Metadata store with section-level dirty tracking and coverage management."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.logging import get_logger
from ..paths import FIXTURES_DIR
from ..constants import RULESETS, SCORE_TYPES
from .models import Metadata

logger = get_logger(__name__)


class MetadataStore:
    """Metadata store with section-level dirty tracking.

    Loads metadata from disk and tracks which sections have been modified.
    Only modified sections are written on save, reducing I/O.
    """

    def __init__(self, fixtures_dir: Path | None = None):
        self.fixtures_dir = fixtures_dir or FIXTURES_DIR
        self.metadata_file = self.fixtures_dir / "metadata.json"
        self._dirty_sections: set[str] = set()
        self._loaded = False

        # Load from disk if exists
        if self.metadata_file.exists():
            self._load()
            self._loaded = True

    def _load(self) -> None:
        """Load metadata from disk."""
        try:
            with open(self.metadata_file) as f:
                data = json.load(f)
            self.data = Metadata.from_dict(data)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to load metadata: {e}")
            self.data = Metadata()

    def save(self) -> None:
        """Save metadata to disk. Only writes if there are dirty sections."""
        if not self._dirty_sections:
            return

        self.data.last_updated = datetime.now(timezone.utc).isoformat()

        # Mark all sections as clean after save
        self._dirty_sections.clear()

        # Write to disk
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.metadata_file, "w") as f:
            json.dump(self.data.to_dict(), f, indent=2)

        logger.debug(f"Metadata saved ({len(self._dirty_sections)} sections changed)")

    def mark_dirty(self, section: str) -> None:
        """Mark a section as dirty so it gets saved."""
        self._dirty_sections.add(section)

    @property
    def samples(self):
        """Access samples section."""
        return self.data.samples

    @property
    def promoted_fixtures(self):
        """Access promoted fixtures section."""
        return self.data.promoted_fixtures

    @property
    def targeted(self):
        """Access targeted metadata section."""
        return self.data.targeted

    @property
    def search_test_coverage(self):
        """Access search test coverage section."""
        return self.data.search_test_coverage

    @property
    def failed_ids(self):
        """Access failed IDs section."""
        return self.data.failed_ids

    @property
    def top_player_ids(self):
        """Access top player IDs section."""
        return self.data.top_player_ids

    @property
    def id_ranges(self):
        """Access ID ranges section."""
        return self.data.id_ranges

    def to_dict(self) -> dict:
        """Get the full metadata as a dictionary (backward compatibility).

        Returns:
            Dictionary representation of all metadata
        """
        return self.data.to_dict()


class FixtureMetadataManager:
    """Handles metadata operations for fixture coverage tracking.

    This is a legacy compatibility class that wraps MetadataStore
    and provides the old API for backward compatibility.
    """

    def __init__(self, metadata: dict | None = None, fixture_dir: Path | None = None):
        self._store = MetadataStore(fixtures_dir=fixture_dir)
        if metadata is not None:
            self.metadata = metadata
        else:
            self.metadata = self._store.data.to_dict()
        self.fixture_dir = fixture_dir or FIXTURES_DIR

    def init_metadata(self):
        """Initialize metadata structure for targeted fixtures."""
        from ..metadata_io import create_targeted_metadata
        if "targeted" not in self.metadata:
            self.metadata["targeted"] = create_targeted_metadata()

    @staticmethod
    def _get_current_timestamp() -> str:
        """Get current UTC timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()

    async def refresh_category_metadata(
        self,
        category: str,
        dry_run: bool = False
    ) -> list[dict]:
        """Refresh metadata for a category to match disk state."""
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
                from ..metadata_io import save_metadata
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
