"""Fixture system for fetching and managing osu! API data.

This package provides tools for:
- Fetching fixtures from the osu! API (beatmaps, beatmapsets, users, scores)
- Managing fixture metadata and coverage tracking
- Generating test fixtures for search engine testing
- Archiving and indexing osu.sh data dumps
"""

from .paths import (
    FIXTURES_DIR,
    TEST_FIXTURES_DIR,
    QUEUE_TEST_FIXTURES_DIR,
    REQUEST_TEST_FIXTURES_DIR,
    get_fixture_path,
    get_test_fixture_path,
)
from .constants import (
    RULESETS,
    SCORE_TYPES,
    ID_RANGES,
    BASE_SAMPLE_COUNTS,
    MINIMAL_PROFILE,
)
from .metadata_io import (
    load_metadata,
    save_metadata,
    create_empty_metadata,
)
from .reader import FixtureReader
from .base_fetcher import BaseFetcher
from .fetcher import FixtureDataFetcher
from .targeted_fetcher import TargetedFixtureFetcher
from .search_test_fetcher import SearchTestFixtureFetcher
from .orchestrator import FixtureOrchestrator
from .criteria import FetchCriteria, FetchReport, Criteria, Source

__all__ = [
    # Paths
    "FIXTURES_DIR",
    "TEST_FIXTURES_DIR",
    "QUEUE_TEST_FIXTURES_DIR",
    "REQUEST_TEST_FIXTURES_DIR",
    "get_fixture_path",
    "get_test_fixture_path",
    # Constants
    "RULESETS",
    "SCORE_TYPES",
    "ID_RANGES",
    "BASE_SAMPLE_COUNTS",
    "MINIMAL_PROFILE",
    # Metadata I/O
    "load_metadata",
    "save_metadata",
    "create_empty_metadata",
    # Readers
    "FixtureReader",
    # Fetchers
    "BaseFetcher",
    "FixtureDataFetcher",
    "TargetedFixtureFetcher",
    "SearchTestFixtureFetcher",
    "FixtureOrchestrator",
    # Criteria
    "FetchCriteria",
    "FetchReport",
    "Criteria",
    "Source",
]
