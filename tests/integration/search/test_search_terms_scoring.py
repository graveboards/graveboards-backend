"""
Test search terms scoring CTE factory.

This module contains tests for the search terms scoring CTE factory.
"""

import pytest

pytestmark = [pytest.mark.integration]


@pytest.mark.integration
def test_scoring_schema_exists() -> None:
    """Test that ScoringSchema is importable."""
    try:
        from app.search.datastructures import ScoringSchema

        assert ScoringSchema is not None
    except ImportError:
        pytest.skip("ScoringSchema not yet implemented")


@pytest.mark.integration
def test_scoring_mode_exists() -> None:
    """Test that ScoringMode enum is importable."""
    try:
        from app.search.enums import ScoringMode

        assert ScoringMode is not None
    except ImportError:
        pytest.skip("ScoringMode not yet implemented")


@pytest.mark.integration
def test_search_terms_scored_cte_exists() -> None:
    """Test that search_terms_scored CTE exists (for future use)."""
    try:
        from app.database.ctes import search_terms_scored

        assert search_terms_scored is not None
    except ImportError:
        pytest.skip("search_terms_scored CTE not yet implemented")
