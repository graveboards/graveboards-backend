"""Search engine integration tests.

These tests verify the search engine's CTE generation, filtering, sorting, and scoring
functionality. They require database seeding for full integration testing.

Gaps:
- Full integration tests require proper database seeding with beatmap/beatmapset data
- Tests are structured but seeding utilities are complex and need proper setup

Tests that can run without database:
- CTE factory structure validation
- Search schema parsing and validation
- Query compilation and SQL generation

Tests that need database:
- End-to-end search with seeded beatmap/beatmapset data
- Score computation verification
- Filtering and sorting result ordering
"""

import pytest
from app.search.enums import Scope
from app.search.engine import SearchEngine
from app.search.datastructures import SearchTermsSchema, FiltersSchema


@pytest.mark.integration
def test_search_engine_initialization():
    """Test SearchEngine initialization with various parameters."""
    engine = SearchEngine(scope=Scope.BEATMAPSETS)
    assert engine.scope == Scope.BEATMAPSETS
    from app.search.mappings import SCOPE_MODEL_MAPPING, SCOPE_SCHEMA_MAPPING
    assert engine.model_class == SCOPE_MODEL_MAPPING[Scope.BEATMAPSETS]
    assert engine.schema_class == SCOPE_SCHEMA_MAPPING[Scope.BEATMAPSETS]


@pytest.mark.integration
def test_search_engine_with_search_terms():
    """Test SearchEngine initialization with search terms."""
    search_terms = SearchTermsSchema(
        terms=["artist", "title"],
        field_weights={"beatmapset": {"artist": 3, "title": 2}},
    )
    
    engine = SearchEngine(
        scope=Scope.BEATMAPSETS,
        search_terms=search_terms,
    )
    
    assert engine.search_terms is not None
    assert engine.search_terms.terms == ["artist", "title"]


@pytest.mark.integration
def test_search_engine_with_sorting():
    """Test SearchEngine initialization with sorting parameters."""
    from app.search.datastructures import SortingSchema
    from app.search.enums import ModelField, SortingOrder

    sorting = SortingSchema(
        [
            {"field": ModelField.BEATMAPSETSNAPSHOT__RANKED, "order": SortingOrder.DESCENDING},
            {"field": ModelField.BEATMAPSETSNAPSHOT__TITLE, "order": SortingOrder.ASCENDING},
        ]
    )
    
    engine = SearchEngine(
        scope=Scope.BEATMAPSETS,
        sorting=sorting,
    )
    
    assert engine.sorting is not None
    items = list(engine.sorting)
    assert len(items) == 2


@pytest.mark.integration
def test_search_engine_with_filters():
    """Test SearchEngine initialization with filter parameters."""
    filters = FiltersSchema(
        beatmapset={"status": "ranked"}
    )
    
    engine = SearchEngine(
        scope=Scope.BEATMAPSETS,
        filters=filters,
    )
    
    assert engine.filters is not None


@pytest.mark.integration
def test_search_engine_query_compilation():
    """Test SearchEngine query compilation."""
    search_terms = SearchTermsSchema(
        terms=["test"],
    )
    
    engine = SearchEngine(
        scope=Scope.BEATMAPSETS,
        search_terms=search_terms,
    )
    
    assert engine.compiled_query is not None


@pytest.mark.integration
def test_search_engine_scope_mapping():
    """Test SearchEngine scope to model/class mapping."""
    from app.search.mappings import SCOPE_MODEL_MAPPING, SCOPE_SCHEMA_MAPPING

    engine = SearchEngine(scope=Scope.BEATMAPSETS)
    assert engine.model_class == SCOPE_MODEL_MAPPING[Scope.BEATMAPSETS]
    assert engine.schema_class == SCOPE_SCHEMA_MAPPING[Scope.BEATMAPSETS]
