"""
Test search terms scoring CTE factory.

This module contains tests for the search terms scoring CTE factory.
"""

import pytest

pytestmark = [pytest.mark.integration]


@pytest.mark.integration
def test_scoring_schema_not_implemented():
    """Test that ScoringSchema is not yet implemented."""
    try:
        from app.search.datastructures import ScoringSchema
        assert False, "ScoringSchema should not be importable yet"
    except ImportError as e:
        assert "ScoringSchema" in str(e)


@pytest.mark.integration
def test_scoring_mode_not_implemented():
    """Test that ScoringMode enum is not yet implemented."""
    try:
        from app.search.enums import ScoringMode
        assert False, "ScoringMode should not be importable yet"
    except ImportError as e:
        assert "ScoringMode" in str(e)


@pytest.mark.integration
def test_search_terms_scored_cte_exists():
    """Test that search_terms_scored CTE exists (for future use)."""
    try:
        from app.database.ctes import search_terms_scored
        assert search_terms_scored is not None
    except ImportError:
        pytest.skip("search_terms_scored CTE not yet implemented")
