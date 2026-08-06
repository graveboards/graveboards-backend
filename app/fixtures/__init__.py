"""Fixture system for fetching and managing osu! API data.

This package provides tools for:
- Fetching fixtures from the osu! API (beatmaps, beatmapsets, users, scores)
- Managing fixture metadata and coverage tracking
- Generating test fixtures for search engine testing
- Archiving and indexing osu.sh data dumps
"""

from __future__ import annotations

from .base_fetcher import BaseFetcher
from .constants import (
    BASE_SAMPLE_COUNTS,
    ID_RANGES,
    MINIMAL_PROFILE,
    RULESETS,
    SCORE_TYPES,
)
from .criteria import Criteria, FetchCriteria, FetchReport, Source
from .fetcher import FixtureDataFetcher
from .metadata_io import (
    create_empty_metadata,
    load_metadata,
    save_metadata,
)
from .orchestrator import FixtureOrchestrator
from .paths import (
    FIXTURES_DIR,
    QUEUE_TEST_FIXTURES_DIR,
    REQUEST_TEST_FIXTURES_DIR,
    TEST_FIXTURES_DIR,
    get_fixture_path,
    get_test_fixture_path,
)
from .reader import FixtureReader
from .search_test_fetcher import SearchTestFixtureFetcher
from .targeted_fetcher import TargetedFixtureFetcher

__all__ = [
    "BASE_SAMPLE_COUNTS",
    # Paths
    "FIXTURES_DIR",
    "ID_RANGES",
    "MINIMAL_PROFILE",
    "QUEUE_TEST_FIXTURES_DIR",
    "REQUEST_TEST_FIXTURES_DIR",
    # Constants
    "RULESETS",
    "SCORE_TYPES",
    "TEST_FIXTURES_DIR",
    # Fetchers
    "BaseFetcher",
    "Criteria",
    # Criteria
    "FetchCriteria",
    "FetchReport",
    "FixtureDataFetcher",
    "FixtureOrchestrator",
    # Readers
    "FixtureReader",
    "SearchTestFixtureFetcher",
    "Source",
    "TargetedFixtureFetcher",
    "create_empty_metadata",
    "get_fixture_path",
    "get_test_fixture_path",
    # Metadata I/O
    "load_metadata",
    "save_metadata",
]
