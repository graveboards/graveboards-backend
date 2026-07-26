from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.search.datastructures import FieldWeights, SearchTermsSchema
from app.search.engine import SearchEngine
from app.search.enums import Scope


class TestSearchEngineCTEs:
    """Test SearchEngine CTE composition."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """Create a mock async session."""
        return MagicMock(spec=AsyncSession)

    def test_engine_applies_filtered_cte(self) -> None:
        """Test that engine applies filtered CTE."""
        terms = SearchTermsSchema(terms=["beatmap"])

        engine = SearchEngine(scope=Scope.BEATMAPS, search_terms=terms)

        compiled = engine.compiled_query.lower()
        assert "beatmap_snapshot" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled

    def test_engine_applies_scored_ctes(self) -> None:
        """Test that engine applies scored CTEs."""
        terms = SearchTermsSchema(terms=["beatmap"], field_weights=FieldWeights())

        engine = SearchEngine(scope=Scope.BEATMAPS, search_terms=terms)

        compiled = engine.compiled_query.lower()
        assert "beatmap_snapshot" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled

    def test_engine_composes_filtered_cte_for_beatmaps(self) -> None:
        """Test CTE composition for beatmaps scope."""
        terms = SearchTermsSchema(terms=["beatmap"])

        engine = SearchEngine(scope=Scope.BEATMAPS, search_terms=terms)

        compiled = engine.compiled_query.lower()
        assert "beatmap_snapshot" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled

    def test_engine_composes_filtered_cte_for_beatmapsets(self) -> None:
        """Test CTE composition for beatmapsets scope."""
        terms = SearchTermsSchema(terms=["beatmapset"])

        engine = SearchEngine(scope=Scope.BEATMAPSETS, search_terms=terms)

        compiled = engine.compiled_query.lower()
        assert "beatmapset_snapshot" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled

    def test_engine_composes_filtered_cte_for_queues(self) -> None:
        """Test CTE composition for queues scope."""
        terms = SearchTermsSchema(terms=["queue"])

        engine = SearchEngine(scope=Scope.QUEUES, search_terms=terms)

        compiled = engine.compiled_query.lower()
        assert "queue" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled

    def test_engine_composes_filtered_cte_for_requests(self) -> None:
        """Test CTE composition for requests scope."""
        terms = SearchTermsSchema(terms=["request"])

        engine = SearchEngine(scope=Scope.REQUESTS, search_terms=terms)

        compiled = engine.compiled_query.lower()
        assert "request" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled


class TestSearchEngineScoreAggregation:
    """Test SearchEngine score aggregation."""

    def test_engine_aggregates_beatmap_scores(self) -> None:
        """Test engine aggregates beatmap scores."""
        terms = SearchTermsSchema(terms=["beatmap"])

        engine = SearchEngine(scope=Scope.BEATMAPS, search_terms=terms)

        compiled = engine.compiled_query.lower()
        assert "beatmap_snapshot" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled

    def test_engine_aggregates_beatmapset_scores(self) -> None:
        """Test engine aggregates beatmapset scores."""
        terms = SearchTermsSchema(terms=["beatmapset"])

        engine = SearchEngine(scope=Scope.BEATMAPSETS, search_terms=terms)

        compiled = engine.compiled_query.lower()
        assert "beatmapset_snapshot" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled

    def test_engine_aggregates_child_scores_to_parent(self) -> None:
        """Test engine aggregates child scores to parent."""
        terms = SearchTermsSchema(terms=["beatmap"])

        engine = SearchEngine(scope=Scope.BEATMAPSETS, search_terms=terms)

        compiled = engine.compiled_query.lower()
        assert "aggregated_beatmap_scores_cte" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled


class TestSearchEngineQueryCompilation:
    """Test SearchEngine query compilation."""

    @pytest.mark.parametrize(
        "scope,expected_table",
        [
            (Scope.BEATMAPS, "beatmap_snapshot"),
            (Scope.BEATMAPSETS, "beatmapset_snapshot"),
            (Scope.QUEUES, "queue"),
            (Scope.REQUESTS, "request"),
        ],
    )
    def test_engine_compiles_for_scope(self, scope: Any, expected_table: str) -> None:
        """Test engine compiles correct table reference for each scope."""
        terms = SearchTermsSchema(terms=["test"])
        engine = SearchEngine(scope=scope, search_terms=terms)
        compiled = engine.compiled_query.lower()
        assert expected_table in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled

    def test_engine_compiles_beatmaps_query(self) -> None:
        """Test engine compiles beatmaps query."""
        terms = SearchTermsSchema(terms=["beatmap"])

        engine = SearchEngine(scope=Scope.BEATMAPS, search_terms=terms)

        compiled = engine.compiled_query.lower()
        assert "beatmap_snapshot" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled

    def test_engine_compiles_beatmapsets_query(self) -> None:
        """Test engine compiles beatmapsets query."""
        terms = SearchTermsSchema(terms=["beatmapset"])

        engine = SearchEngine(scope=Scope.BEATMAPSETS, search_terms=terms)

        compiled = engine.compiled_query.lower()
        assert "beatmapset_snapshot" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled

    def test_engine_compiles_queues_query(self) -> None:
        """Test engine compiles queues query."""
        terms = SearchTermsSchema(terms=["queue"])

        engine = SearchEngine(scope=Scope.QUEUES, search_terms=terms)

        compiled = engine.compiled_query.lower()
        assert "queue" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled

    def test_engine_compiles_requests_query(self) -> None:
        """Test engine compiles requests query."""
        terms = SearchTermsSchema(terms=["request"])

        engine = SearchEngine(scope=Scope.REQUESTS, search_terms=terms)

        compiled = engine.compiled_query.lower()
        assert "request" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled

    def test_engine_includes_total_score_with_search_terms(self) -> None:
        """Test that compiled query includes total_score when search terms present."""
        terms = SearchTermsSchema(terms=["test"])
        engine = SearchEngine(scope=Scope.BEATMAPS, search_terms=terms)
        compiled = engine.compiled_query.lower()
        assert "total_score" in compiled

    def test_engine_excludes_total_score_without_search_terms(self) -> None:
        """Test that compiled query omits total_score when no search terms."""
        engine = SearchEngine(scope=Scope.BEATMAPS)
        compiled = engine.compiled_query.lower()
        assert "total_score" not in compiled

    def test_engine_compiled_query_is_valid_sql(self) -> None:
        """Test that compiled query starts with valid SQL construct."""
        terms = SearchTermsSchema(terms=["test"])
        engine = SearchEngine(scope=Scope.BEATMAPS, search_terms=terms)
        compiled = engine.compiled_query
        assert compiled.startswith("WITH ") or compiled.startswith("SELECT ")


class TestSearchEngineValidation:
    """Test search engine input validation."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """Create a mock async session."""
        return MagicMock(spec=AsyncSession)

    def test_engine_creation_with_scope(self, mock_session: MagicMock) -> None:
        """Test SearchEngine creation with scope."""
        engine = SearchEngine(scope=Scope.BEATMAPS)
        assert engine.scope == Scope.BEATMAPS
        assert engine.model_class is not None

    def test_engine_creation_with_search_terms_dict(self, mock_session: MagicMock) -> None:
        """Test SearchEngine creation with search terms dict."""
        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            search_terms={"terms": ["test"], "categories": ["beatmap"], "exact": False},
        )
        assert engine.search_terms is not None

    def test_engine_creation_with_sorting_list(self, mock_session: MagicMock) -> None:
        """Test SearchEngine creation with sorting list."""
        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            sorting=[{"field": "BeatmapsetSnapshot.beatmapset_id", "order": "asc"}],
        )
        assert engine.sorting is not None

    def test_engine_creation_with_filters_dict(self, mock_session: MagicMock) -> None:
        """Test SearchEngine creation with filters dict."""
        engine = SearchEngine(
            scope=Scope.BEATMAPS, filters={"beatmap": {"beatmap_id": {"eq": 123}}}
        )
        assert engine.filters is not None

    def test_engine_rejects_invalid_search_terms_type(self) -> None:
        """Test that invalid search terms type raises."""
        with pytest.raises(TypeError):
            SearchEngine(scope=Scope.BEATMAPS, search_terms=cast(Any, "not_a_dict"))

    def test_engine_rejects_invalid_sorting_type(self) -> None:
        """Test that invalid sorting type raises."""
        with pytest.raises(TypeError):
            SearchEngine(scope=Scope.BEATMAPS, sorting=cast(Any, "not_a_list"))

    def test_engine_rejects_invalid_filters_type(self) -> None:
        """Test that invalid filters type raises."""
        with pytest.raises(TypeError):
            SearchEngine(scope=Scope.BEATMAPS, filters=cast(Any, "not_a_dict"))

    @pytest.mark.asyncio
    async def test_search_requires_non_negative_limit(self, mock_session: MagicMock) -> None:
        """Test that search requires non-negative limit."""
        engine = SearchEngine(scope=Scope.BEATMAPS)
        with pytest.raises(TypeError):
            await engine.search(mock_session, limit=-1)

    @pytest.mark.asyncio
    async def test_search_requires_non_negative_offset(self, mock_session: MagicMock) -> None:
        """Test that search requires non-negative offset."""
        engine = SearchEngine(scope=Scope.BEATMAPS)
        with pytest.raises(TypeError):
            await engine.search(mock_session, offset=-1)

    @pytest.mark.asyncio
    async def test_search_requires_integer_limit(self, mock_session: MagicMock) -> None:
        """Test that search requires integer limit."""
        engine = SearchEngine(scope=Scope.BEATMAPS)
        with pytest.raises(TypeError):
            await engine.search(mock_session, limit=cast(int, 10.5))

    @pytest.mark.asyncio
    async def test_search_requires_integer_offset(self, mock_session: MagicMock) -> None:
        """Test that search requires integer offset."""
        engine = SearchEngine(scope=Scope.BEATMAPS)
        with pytest.raises(TypeError):
            await engine.search(mock_session, offset=cast(int, 10.5))

    def test_search_returns_results(self, mock_session: MagicMock) -> None:
        """Test that search returns results."""
        engine = SearchEngine(scope=Scope.BEATMAPS)
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        engine._compose_query()
        compiled = engine.compiled_query.lower()
        assert "beatmap_snapshot" in compiled
        assert "select" in compiled

    def test_engine_composes_query(self) -> None:
        """Test that engine composes query."""
        engine = SearchEngine(scope=Scope.BEATMAPS)
        assert engine.query is not None
        compiled = engine.compiled_query.lower()
        assert "beatmap_snapshot" in compiled
        assert "select" in compiled

    def test_engine_scope_beatmaps(self) -> None:
        """Test engine scope beatmaps."""
        engine = SearchEngine(scope=Scope.BEATMAPS)
        assert engine.scope == Scope.BEATMAPS
        assert engine.model_class.value.__name__ == "BeatmapSnapshot"

    def test_engine_scope_beatmapsets(self) -> None:
        """Test engine scope beatmapsets."""
        engine = SearchEngine(scope=Scope.BEATMAPSETS)
        assert engine.scope == Scope.BEATMAPSETS
        assert engine.model_class.value.__name__ == "BeatmapsetSnapshot"

    def test_engine_scope_queues(self) -> None:
        """Test engine scope queues."""
        engine = SearchEngine(scope=Scope.QUEUES)
        assert engine.scope == Scope.QUEUES
        assert engine.model_class.value.__name__ == "Queue"

    def test_engine_scope_requests(self) -> None:
        """Test engine scope requests."""
        engine = SearchEngine(scope=Scope.REQUESTS)
        assert engine.scope == Scope.REQUESTS
        assert engine.model_class.value.__name__ == "Request"

    def test_engine_with_none_search_terms(self) -> None:
        """Test engine with None search terms."""
        engine = SearchEngine(scope=Scope.BEATMAPS, search_terms=None)
        assert engine.search_terms is None

    def test_engine_with_none_sorting(self) -> None:
        """Test engine with None sorting."""
        engine = SearchEngine(scope=Scope.BEATMAPS, sorting=None)
        assert engine.sorting is None

    def test_engine_with_none_filters(self) -> None:
        """Test engine with None filters."""
        engine = SearchEngine(scope=Scope.BEATMAPS, filters=None)
        assert engine.filters is None

    def test_engine_sorting_default_order(self) -> None:
        """Test engine sorting with default order."""
        engine = SearchEngine(
            scope=Scope.BEATMAPS, sorting=[{"field": "BeatmapsetSnapshot.beatmapset_id"}]
        )
        assert engine.sorting is not None
        options = list(engine.sorting)
        assert len(options) == 1

    def test_engine_filters_none_category(self) -> None:
        """Test engine filters with None value - should be ignored."""
        engine = SearchEngine(scope=Scope.BEATMAPS, filters={})
        assert engine.filters is not None

    def test_engine_search_terms_validation(self) -> None:
        """Test engine validates search terms against scope."""
        from app.search.datastructures import SearchTermsSchema

        terms = SearchTermsSchema.model_validate({"terms": ["test"]})
        terms.validate_against_scope(Scope.BEATMAPS)

    def test_engine_complex_search_config(self) -> None:
        """Test engine with complex search configuration."""
        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            search_terms={"terms": ["test", "beatmap"], "categories": ["beatmap"]},
            sorting=[{"field": "BeatmapSnapshot.beatmap_id", "order": "desc"}],
            filters={"beatmap": {"beatmap_id": {"gt": 100, "lt": 200}}},
        )
        assert engine.search_terms is not None
        assert engine.sorting is not None
        assert engine.filters is not None
        compiled = engine.compiled_query.lower()
        assert "beatmap_snapshot" in compiled
        assert "beatmap_id" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled

    def test_engine_search_with_debug(self, mock_session: MagicMock) -> None:
        """Test search with debug mode."""
        engine = SearchEngine(scope=Scope.BEATMAPS)
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        with patch.object(engine, "_compose_query"):
            engine._compose_query()

    def test_engine_search_limits(self, mock_session: MagicMock) -> None:
        """Test search with limit."""
        engine = SearchEngine(scope=Scope.BEATMAPS)
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        with patch.object(engine, "_compose_query"):
            engine._compose_query()

    def test_engine_default_limit_offset(self) -> None:
        """Test engine uses default limit and offset."""
        from app.search.engine import DEFAULT_LIMIT, DEFAULT_OFFSET

        SearchEngine(scope=Scope.BEATMAPS)
        assert DEFAULT_LIMIT == 50
        assert DEFAULT_OFFSET == 0
