"""Metadata store with section-level dirty tracking."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.logging import get_logger
from ..paths import FIXTURES_DIR
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
