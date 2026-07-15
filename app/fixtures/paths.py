"""Path constants and utilities for fixture file locations."""

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


def get_fixture_path(category: str, subcategory: str | None = None, fixtures_dir: Path | None = None) -> Path:
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
