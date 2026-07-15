"""Shared helpers for fixture promotion and demotion."""
from datetime import datetime, timezone
from shutil import copy2, rmtree

from rich.console import Console

from app.fixtures.metadata_io import create_empty_samples
from app.fixtures.paths import (
    FIXTURES_DIR,
    QUEUE_TEST_FIXTURES_DIR,
    REQUEST_TEST_FIXTURES_DIR,
    TEST_FIXTURES_DIR,
)

console = Console()


def _get_dst_path(category: str) -> str:
    """Get destination path for a category."""
    if category == "queues":
        return str(QUEUE_TEST_FIXTURES_DIR)
    elif category == "requests":
        return str(REQUEST_TEST_FIXTURES_DIR)
    else:
        return str(TEST_FIXTURES_DIR / category)


def _move_fixture_files(
    categories: list[str],
    src_base: str,
    dst_base: str,
    metadata: dict,
    action: str = "promote",
) -> int:
    """Move fixture files between directories with proper metadata tracking.
    
    Args:
        categories: List of category names to move
        src_base: Source base path
        dst_base: Destination base path
        metadata: Metadata dict to update
        action: "promote" or "demote"
        
    Returns:
        Number of files moved
    """
    current_time = datetime.now(timezone.utc).isoformat()
    copied = 0
    deleted = 0

    src_path_base = FIXTURES_DIR if src_base == "instance" else TEST_FIXTURES_DIR
    dst_path_base = TEST_FIXTURES_DIR if dst_base == "tests" else FIXTURES_DIR

    # Phase 1: Collect all copy operations
    copy_operations = []

    for category in categories:
        src_path = src_path_base / category
        
        if category == "queues":
            dst_path = QUEUE_TEST_FIXTURES_DIR
        elif category == "requests":
            dst_path = REQUEST_TEST_FIXTURES_DIR
        else:
            dst_path = dst_path_base / category

        dst_path.mkdir(parents=True, exist_ok=True)

        if category in ["beatmaps", "beatmapsets", "beatmap_scores", "beatmap_attributes", "queues", "requests"]:
            if src_path.exists():
                for filepath in src_path.glob("*.json"):
                    copy_operations.append((filepath, dst_path / filepath.name, category, None))
        elif category in ["users", "scores"]:
            if src_path.exists():
                for sub in src_path.iterdir():
                    if sub.is_dir():
                        sub_dst = dst_path / sub.name
                        sub_dst.mkdir(parents=True, exist_ok=True)
                        for filepath in sub.glob("*.json"):
                            copy_operations.append((filepath, sub_dst / filepath.name, category, sub.name))

    # Phase 2: Execute all copy operations
    for src, dst, _, _ in copy_operations:
        copy2(src, dst)
        copied += 1

    # Phase 3: Update metadata and delete sources
    for category in categories:
        src_path = src_path_base / category
        
        if category == "queues":
            dst_path = QUEUE_TEST_FIXTURES_DIR
        elif category == "requests":
            dst_path = REQUEST_TEST_FIXTURES_DIR
        else:
            dst_path = dst_path_base / category

        if category in ["beatmaps", "beatmapsets", "beatmap_scores", "beatmap_attributes", "queues", "requests"]:
            count = 0
            if src_path.exists():
                count = len(list(src_path.glob("*.json")))
                rmtree(src_path)
                deleted += count
            if category not in metadata.get("promoted_fixtures", {}):
                metadata.setdefault("promoted_fixtures", {})[category] = {"count": 0, "last_promoted": None}
            metadata["promoted_fixtures"][category]["count"] = metadata["promoted_fixtures"][category].get("count", 0) + count
            metadata["promoted_fixtures"][category]["last_promoted"] = current_time
        elif category in ["users", "scores"]:
            total_count = 0
            if src_path.exists():
                for sub in src_path.iterdir():
                    if sub.is_dir():
                        count = len(list(sub.glob("*.json")))
                        total_count += count
                        rmtree(sub)
                        deleted += count
                        if category == "users":
                            metadata.setdefault("promoted_fixtures", {}).setdefault(category, {"count": 0, "per_ruleset": {}})
                            metadata["promoted_fixtures"][category].setdefault("per_ruleset", {})
                            metadata["promoted_fixtures"][category]["per_ruleset"][sub.name] = metadata["promoted_fixtures"][category]["per_ruleset"].get(sub.name, 0) + count
                        else:
                            metadata.setdefault("promoted_fixtures", {}).setdefault(category, {"count": 0, "per_type": {}})
                            metadata["promoted_fixtures"][category].setdefault("per_type", {})
                            metadata["promoted_fixtures"][category]["per_type"][sub.name] = metadata["promoted_fixtures"][category]["per_type"].get(sub.name, 0) + count
                if src_path.exists():
                    src_path.rmdir()
                metadata.setdefault("promoted_fixtures", {}).setdefault(category, {"count": 0})
                metadata["promoted_fixtures"][category]["count"] = metadata["promoted_fixtures"][category].get("count", 0) + total_count
                metadata["promoted_fixtures"][category]["last_promoted"] = current_time

    return copied
