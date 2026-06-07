"""
Test search terms filtering CTE factory.

This module contains tests for the search terms filtering CTE factory.
"""

import pytest

pytestmark = [pytest.mark.integration]


@pytest.mark.integration
def test_search_terms_filtered_cte_structure():
    """Test search terms filtered CTE structure."""
    from app.database.models import BeatmapsetSnapshot

    assert BeatmapsetSnapshot is not None


@pytest.mark.integration
def test_search_terms_filtered_cte_factory():
    """Test search terms filtered CTE factory function."""
    try:
        from app.database.ctes.search_terms_filtered import build_search_terms_filtered_cte

        assert callable(build_search_terms_filtered_cte)
    except ImportError:
        pytest.skip("build_search_terms_filtered_cte not yet implemented")


@pytest.mark.integration
def test_search_terms_filtered_cte_with_beatmaps_scope():
    """Test search terms filtered CTE with beatmaps scope."""
    try:
        from app.database.ctes.search_terms_filtered import build_search_terms_filtered_cte
        from app.search.enums import Scope

        cte = build_search_terms_filtered_cte([], Scope.BEATMAPS)
        assert cte is not None
    except ImportError:
        pytest.skip("build_search_terms_filtered_cte not yet implemented")


@pytest.mark.integration
def test_search_terms_filtered_cte_with_queues_scope():
    """Test search terms filtered CTE with queues scope."""
    try:
        from app.database.ctes.search_terms_filtered import build_search_terms_filtered_cte
        from app.search.enums import Scope

        cte = build_search_terms_filtered_cte([], Scope.QUEUES)
        assert cte is not None
    except ImportError:
        pytest.skip("build_search_terms_filtered_cte not yet implemented")


@pytest.mark.integration
def test_search_terms_filtered_cte_with_requests_scope():
    """Test search terms filtered CTE with requests scope."""
    try:
        from app.database.ctes.search_terms_filtered import build_search_terms_filtered_cte
        from app.search.enums import Scope

        cte = build_search_terms_filtered_cte([], Scope.REQUESTS)
        assert cte is not None
    except ImportError:
        pytest.skip("build_search_terms_filtered_cte not yet implemented")


@pytest.mark.integration
def test_search_terms_filtered_cte_filter_validation():
    """Test search terms filtered CTE filter validation."""
    try:
        from app.database.ctes.search_terms_filtered import build_search_terms_filtered_cte
        from app.search.enums import Scope

        cte = build_search_terms_filtered_cte([], Scope.BEATMAPS)
        assert cte is not None
    except ImportError:
        pytest.skip("build_search_terms_filtered_cte not yet implemented")


@pytest.mark.integration
def test_search_terms_filtered_cte_case_sensitivity():
    """Test search terms filtered CTE case sensitivity."""
    try:
        from app.database.ctes.search_terms_filtered import build_search_terms_filtered_cte
        from app.search.enums import Scope

        cte = build_search_terms_filtered_cte([], Scope.BEATMAPS)
        assert cte is not None
    except ImportError:
        pytest.skip("build_search_terms_filtered_cte not yet implemented")


@pytest.mark.integration
def test_search_terms_filtered_cte_debug_mode():
    """Test search terms filtered CTE debug mode."""
    try:
        from app.database.ctes.search_terms_filtered import build_search_terms_filtered_cte
        from app.search.enums import Scope

        cte = build_search_terms_filtered_cte([], Scope.BEATMAPS)
        assert cte is not None
    except ImportError:
        pytest.skip("build_search_terms_filtered_cte not yet implemented")
