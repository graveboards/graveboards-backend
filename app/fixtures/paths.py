"""Path constants and utilities for fixture file locations.

File naming convention:
    beatmaps:        beatmap_{id}.json
    beatmapsets:     beatmapset_{id}.json
    users:           user_{id}_{ruleset}.json (in users/{ruleset}/)
    scores:          scores_{id}_{type}.json (in scores/{type}/)
    beatmap_scores:  beatmap_scores_{id}.json
    beatmap_attributes: beatmap_attrs_{id}_mods{mods}.json
"""

from pathlib import Path
from app.config import PROJECT_ROOT

# Instance fixtures (production API-fetched data)
FIXTURES_DIR = PROJECT_ROOT / "instance" / "fixtures"
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

# Test fixtures (used by pytest tests)
TEST_FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures" / "osu"
TEST_FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

# Queue and request test fixtures
QUEUE_TEST_FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures" / "queues"
QUEUE_TEST_FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

REQUEST_TEST_FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures" / "requests"
REQUEST_TEST_FIXTURES_DIR.mkdir(parents=True, exist_ok=True)


def get_test_fixture_path(category: str, subcategory: str | None = None) -> Path:
    """Get path to test fixture directory."""
    path = TEST_FIXTURES_DIR / category
    if subcategory:
        path = path / subcategory
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_fixture_path(
    category: str, subcategory: str | None = None, fixtures_dir: Path | None = None
) -> Path:
    """Get path to fixture directory.

    Args:
        category: Fixture category (e.g., "beatmaps", "users")
        subcategory: Optional subcategory (e.g., "osu" for users, "best" for scores)
        fixtures_dir: Override base directory (defaults to FIXTURES_DIR)
    """
    base = fixtures_dir or FIXTURES_DIR
    path = base / category
    if subcategory:
        path = path / subcategory
    path.mkdir(parents=True, exist_ok=True)
    return path
