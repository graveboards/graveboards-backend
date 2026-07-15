"""Compatibility shim for legacy utils.py imports.

This module re-exports everything from the new split modules for backward compatibility.
All new code should import directly from the specific modules (paths, constants, metadata_io, sample_counts).
"""

# Paths
from app.fixtures.paths import (
    FIXTURES_DIR,
    TEST_FIXTURES_DIR,
    QUEUE_TEST_FIXTURES_DIR,
    REQUEST_TEST_FIXTURES_DIR,
    get_fixture_path,
    get_test_fixture_path,
)

# Constants
from app.fixtures.constants import (
    RULESETS,
    SCORE_TYPES,
    ID_RANGES,
    ID_RANGE_MIN,
    TOP_PLAYERS_PER_RULESET,
    RANKING_PAGE_SIZE,
    MAX_RETRIES,
    MAX_RETRIES_SCORES,
    BASE_SAMPLE_COUNTS,
    MINIMAL_PROFILE,
    DISCUSSION_STATUSES,
    REQUEST_STATUSES,
    REQUEST_STATUS_NAMES,
    BEATMAP_STATUSES,
    BEATMAP_STATUS_NAMES,
    BEATMAP_MODES,
    BEATMAP_MODE_NAMES,
    GENRE_IDS,
    GENRE_NAMES,
    LANGUAGE_IDS,
    LANGUAGE_NAMES,
    COUNTRY_CODES,
)

# Metadata I/O
from app.fixtures.metadata_io import (
    load_metadata,
    save_metadata,
    create_empty_metadata,
    create_empty_samples,
    create_empty_promoted_fixtures,
    create_targeted_metadata,
    load_top_player_ids,
    save_top_player_ids,
    wipe_all_fixtures,
    get_fixture_count,
    get_all_fixture_files,
)

# Sample counts
from app.fixtures.sample_counts import calculate_sample_counts
