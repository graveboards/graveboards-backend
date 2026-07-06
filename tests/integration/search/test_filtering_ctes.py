"""Search filtering CTE tests.

These tests verify the search term filtering functionality that ensures all search terms
must match (AND logic) across the appropriate field categories.
"""

import pytest
from sqlalchemy.dialects import postgresql
from app.search.enums import Scope
from app.database.ctes.search_terms_filtered import search_terms_filtered_cte_factory
from app.search.datastructures import SearchTermsSchema


def _compile_postgres(cte):
    """Compile a CTE with PostgreSQL dialect for accurate SQL inspection."""
    return str(cte.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": True}
    )).lower()


@pytest.mark.integration
def test_search_terms_filtered_cte_creation():
    """Test filtering CTE factory creates valid CTE structure."""
    search_terms = SearchTermsSchema(
        terms=["artist", "title"],
        field_weights={"beatmapset": {"artist": 3, "title": 2}},
    )

    cte = search_terms_filtered_cte_factory(Scope.BEATMAPSETS, search_terms)

    assert cte is not None
    assert hasattr(cte, "c")
    assert hasattr(cte.c, "id")
    compiled = _compile_postgres(cte)
    assert "beatmapset_snapshot" in compiled
    assert "ilike" in compiled


@pytest.mark.integration
def test_search_terms_filtered_single_term():
    """Test filtering CTE with a single search term."""
    search_terms = SearchTermsSchema(
        terms=["test"],
        field_weights={"beatmapset": {"artist": 3}},
    )

    cte = search_terms_filtered_cte_factory(Scope.BEATMAPSETS, search_terms)

    assert cte is not None
    assert hasattr(cte.c, "id")
    compiled = _compile_postgres(cte)
    assert "ilike" in compiled


@pytest.mark.integration
def test_search_terms_filtered_beatmaps_scope():
    """Test filtering CTE with BEATMAPS scope."""
    search_terms = SearchTermsSchema(
        terms=["version"],
        field_weights={"beatmap": {"version": 3}},
    )

    cte = search_terms_filtered_cte_factory(Scope.BEATMAPS, search_terms)

    assert cte is not None
    assert hasattr(cte.c, "id")
    compiled = _compile_postgres(cte)
    assert "beatmap_snapshot" in compiled
    assert "ilike" in compiled


@pytest.mark.integration
def test_search_terms_filtered_case_sensitive():
    """Test filtering CTE with case sensitive flag."""
    search_terms = SearchTermsSchema(
        terms=["ARTIST"],
        field_weights={"beatmapset": {"artist": 3}},
        case_sensitive=True,
    )

    cte = search_terms_filtered_cte_factory(Scope.BEATMAPSETS, search_terms)

    assert cte is not None
    assert hasattr(cte.c, "id")
    compiled = _compile_postgres(cte)
    assert "like " in compiled
    assert "ilike" not in compiled


@pytest.mark.integration
def test_search_terms_filtered_no_match():
    """Test filtering CTE with term that won't match."""
    search_terms = SearchTermsSchema(
        terms=["nonexistent_xyz_123"],
        field_weights={"beatmapset": {"artist": 3}},
    )

    cte = search_terms_filtered_cte_factory(Scope.BEATMAPSETS, search_terms)

    assert cte is not None
    assert hasattr(cte.c, "id")
    compiled = _compile_postgres(cte)
    assert "nonexistent_xyz_123" in compiled
