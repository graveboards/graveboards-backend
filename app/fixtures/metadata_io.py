"""Metadata I/O operations for fixture tracking."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from typing import cast as typing_cast

from app.observability.logging import get_logger

from .constants import ID_RANGES, RULESETS, SCORE_TYPES
from .paths import FIXTURES_DIR

if TYPE_CHECKING:
    from pathlib import Path

logger = get_logger(__name__)

METADATA_FILE = FIXTURES_DIR / "metadata.json"


def _metadata_path(fixtures_dir: Path | None = None) -> Path:
    """Get path to metadata file."""
    base = fixtures_dir or FIXTURES_DIR
    return base / "metadata.json"


def load_metadata(fixtures_dir: Path | None = None) -> dict[str, Any]:
    """Load metadata from disk.

    Args:
        fixtures_dir: Override base directory (defaults to FIXTURES_DIR)

    Returns:
    -------
        Metadata dictionary
    """
    metadata_file = _metadata_path(fixtures_dir)
    if metadata_file.exists():
        with metadata_file.open() as f:
            data: dict[str, Any] = json.load(f)
        return data
    return create_empty_metadata()


def save_metadata(metadata: dict[str, Any], fixtures_dir: Path | None = None) -> None:
    """Save metadata to disk.

    Args:
        metadata: Metadata dictionary to save
        fixtures_dir: Override base directory (defaults to FIXTURES_DIR)
    """
    metadata["last_updated"] = datetime.now(UTC).isoformat()
    metadata.setdefault(
        "promoted_fixtures",
        {
            "beatmaps": {"count": 0, "last_promoted": None},
            "beatmapsets": {"count": 0, "last_promoted": None},
            "users": {"count": 0, "per_ruleset": dict.fromkeys(RULESETS, 0), "last_promoted": None},
            "scores": {
                "count": 0,
                "per_type": dict.fromkeys(SCORE_TYPES, 0),
                "last_promoted": None,
            },
            "beatmap_scores": {"count": 0, "last_promoted": None},
            "beatmap_attributes": {"count": 0, "last_promoted": None},
            "queues": {"count": 0, "last_promoted": None},
            "requests": {"count": 0, "last_promoted": None},
        },
    )
    metadata.setdefault(
        "fetched_ids",
        {
            "beatmaps": [],
            "beatmapsets": [],
            "users": {r: [] for r in RULESETS},
        },
    )
    metadata.setdefault("top_player_ids", {r: [] for r in RULESETS})
    metadata.setdefault("id_ranges", ID_RANGES.copy())
    metadata_file = _metadata_path(fixtures_dir)
    metadata_file.parent.mkdir(parents=True, exist_ok=True)
    with metadata_file.open("w") as f:
        json.dump(metadata, f, indent=2)


def create_empty_metadata() -> dict[str, Any]:
    """Create empty metadata structure.

    Returns:
    -------
        Empty metadata dictionary
    """
    return {
        "last_updated": None,
        "samples": {
            "beatmaps": {"count": 0, "last_fetched": None},
            "beatmapsets": {"count": 0, "last_fetched": None},
            "users": {"count": 0, "per_ruleset": dict.fromkeys(RULESETS, 0), "last_fetched": None},
            "scores": {"count": 0, "per_type": dict.fromkeys(SCORE_TYPES, 0), "last_fetched": None},
            "beatmap_scores": {"count": 0, "last_fetched": None},
            "beatmap_attributes": {"count": 0, "last_fetched": None},
            "queues": {"count": 0, "last_fetched": None},
            "requests": {"count": 0, "last_fetched": None},
        },
        "promoted_fixtures": {
            "beatmaps": {"count": 0, "last_promoted": None},
            "beatmapsets": {"count": 0, "last_promoted": None},
            "users": {"count": 0, "per_ruleset": dict.fromkeys(RULESETS, 0), "last_promoted": None},
            "scores": {
                "count": 0,
                "per_type": dict.fromkeys(SCORE_TYPES, 0),
                "last_promoted": None,
            },
            "beatmap_scores": {"count": 0, "last_promoted": None},
            "beatmap_attributes": {"count": 0, "last_promoted": None},
            "queues": {"count": 0, "last_promoted": None},
            "requests": {"count": 0, "last_promoted": None},
        },
        "failed_ids": {
            "beatmaps": [],
            "beatmapsets": [],
            "users": {r: [] for r in RULESETS},
        },
        "top_player_ids": {r: [] for r in RULESETS},
        "id_ranges": ID_RANGES,
        "rulesets": RULESETS,
        "source": "osu.ppy.sh/api/v2",
    }


def create_empty_samples() -> dict[str, Any]:
    """Create empty samples structure.

    Returns:
    -------
        Empty samples dictionary
    """
    return {
        "beatmaps": {"count": 0, "last_fetched": None},
        "beatmapsets": {"count": 0, "last_fetched": None},
        "users": {"count": 0, "per_ruleset": dict.fromkeys(RULESETS, 0), "last_fetched": None},
        "scores": {"count": 0, "per_type": dict.fromkeys(SCORE_TYPES, 0), "last_fetched": None},
        "beatmap_scores": {"count": 0, "last_fetched": None},
        "beatmap_attributes": {"count": 0, "last_fetched": None},
        "queues": {"count": 0, "last_fetched": None},
        "requests": {"count": 0, "last_fetched": None},
    }


def create_empty_promoted_fixtures() -> dict[str, Any]:
    """Create empty promoted fixtures structure.

    Returns:
    -------
        Empty promoted fixtures dictionary
    """
    return {
        "beatmaps": {"count": 0, "last_promoted": None},
        "beatmapsets": {"count": 0, "last_promoted": None},
        "users": {"count": 0, "per_ruleset": dict.fromkeys(RULESETS, 0), "last_promoted": None},
        "scores": {"count": 0, "per_type": dict.fromkeys(SCORE_TYPES, 0), "last_promoted": None},
        "beatmap_scores": {"count": 0, "last_promoted": None},
        "beatmap_attributes": {"count": 0, "last_promoted": None},
        "queues": {"count": 0, "last_promoted": None},
        "requests": {"count": 0, "last_promoted": None},
    }


def load_top_player_ids(fixtures_dir: Path | None = None) -> dict[str, list[int]]:
    """Load top player IDs from metadata.

    Args:
        fixtures_dir: Override base directory (defaults to FIXTURES_DIR)

    Returns:
    -------
        Dictionary mapping rulesets to lists of player IDs
    """
    metadata = load_metadata(fixtures_dir=fixtures_dir)
    return typing_cast(
        "dict[str, list[int]]", metadata.get("top_player_ids", {r: [] for r in RULESETS})
    )


def save_top_player_ids(
    top_player_ids: dict[str, list[int]], fixtures_dir: Path | None = None
) -> None:
    """Save top player IDs to metadata.

    Args:
        top_player_ids: Dictionary mapping rulesets to lists of player IDs
        fixtures_dir: Override base directory (defaults to FIXTURES_DIR)
    """
    metadata = load_metadata(fixtures_dir=fixtures_dir)
    metadata["top_player_ids"] = top_player_ids
    save_metadata(metadata, fixtures_dir=fixtures_dir)


def clean_all_fixtures(
    clear_failed_ids: bool = False,
    clear_top_player_ids: bool = False,
    fixtures_dir: Path | None = None,
) -> None:
    """Clean all fixture files and reset metadata.

    Args:
        clear_failed_ids: If True, also clear failed IDs
        clear_top_player_ids: If True, also clear top player IDs
        fixtures_dir: Override base directory (defaults to FIXTURES_DIR)
    """
    base = fixtures_dir or FIXTURES_DIR
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True, exist_ok=True)

    metadata = create_empty_metadata()
    metadata_file = _metadata_path(fixtures_dir)
    if not clear_failed_ids and metadata_file.exists():
        existing_metadata = load_metadata(fixtures_dir=fixtures_dir)
        metadata["failed_ids"] = existing_metadata.get("failed_ids", metadata["failed_ids"])
    if not clear_top_player_ids and metadata_file.exists():
        existing_metadata = load_metadata(fixtures_dir=fixtures_dir)
        metadata["top_player_ids"] = existing_metadata.get(
            "top_player_ids", metadata["top_player_ids"]
        )

    save_metadata(metadata, fixtures_dir=fixtures_dir)
    logger.info("All fixtures cleaned")


def get_fixture_count(
    category: str, subcategory: str | None = None, fixtures_dir: Path | None = None
) -> int:
    """Get count of fixture files in a category.

    Args:
        category: Fixture category (e.g., "beatmaps", "users")
        subcategory: Optional subcategory (e.g., "osu" for users, "best" for scores)
        fixtures_dir: Override base directory (defaults to FIXTURES_DIR)

    Returns:
    -------
        Number of JSON files in the category directory
    """
    from .paths import get_fixture_path

    path = get_fixture_path(category, subcategory, fixtures_dir=fixtures_dir)
    if not path.exists():
        return 0
    return len(list(path.glob("*.json")))


def get_all_fixture_files(
    fixtures_dir: Path | None = None,
) -> dict[str, list[Path] | dict[str, list[Path]]]:
    """Get all fixture files organized by category.

    Args:
        fixtures_dir: Override base directory (defaults to FIXTURES_DIR)

    Returns:
    -------
        Dictionary mapping category names to lists of file paths
    """
    from .paths import FIXTURES_DIR

    base = fixtures_dir or FIXTURES_DIR
    fixtures: dict[str, list[Path] | dict[str, list[Path]]] = {}
    for category in [
        "beatmaps",
        "beatmapsets",
        "beatmap_scores",
        "beatmap_attributes",
        "queues",
        "requests",
    ]:
        path = base / category
        if path.exists():
            fixtures[category] = list(path.glob("*.json"))
    for category in ["users", "scores"]:
        path = base / category
        if path.exists():
            sub_fixtures: dict[str, list[Path]] = {}
            for sub in path.iterdir():
                if sub.is_dir():
                    sub_fixtures[sub.name] = list(sub.glob("*.json"))
            fixtures[category] = sub_fixtures
    return fixtures


def create_targeted_metadata() -> dict[str, Any]:
    """Create the standard targeted fixtures metadata structure.

    Returns:
    -------
        Targeted metadata dictionary
    """
    return {
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
        "queues": {
            "by_visibility": {},
            "by_is_open": {},
            "file_metadata": {},
        },
        "requests": {
            "by_status": {},
            "by_mv_checked": {},
            "file_metadata": {},
        },
    }
