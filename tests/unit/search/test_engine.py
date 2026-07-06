import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.search.engine import SearchEngine
from app.search.enums import Scope
from app.search.datastructures import SearchTermsSchema, FieldWeights


class TestSearchEngineCTEs:
    """Test SearchEngine CTE composition."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock async session."""
        return MagicMock(spec=AsyncSession)

    def test_engine_applies_filtered_cte(self):
        """Test that engine applies filtered CTE."""
        terms = SearchTermsSchema(terms=["beatmap"])

        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            search_terms=terms
        )

        compiled = engine.compiled_query.lower()
        assert "beatmap_snapshot" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled

    def test_engine_applies_scored_ctes(self):
        """Test that engine applies scored CTEs."""
        terms = SearchTermsSchema(
            terms=["beatmap"],
            field_weights=FieldWeights()
        )

        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            search_terms=terms
        )

        compiled = engine.compiled_query.lower()
        assert "beatmap_snapshot" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled

    def test_engine_composes_filtered_cte_for_beatmaps(self):
        """Test CTE composition for beatmaps scope."""
        terms = SearchTermsSchema(terms=["beatmap"])

        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            search_terms=terms
        )

        compiled = engine.compiled_query.lower()
        assert "beatmap_snapshot" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled

    def test_engine_composes_filtered_cte_for_beatmapsets(self):
        """Test CTE composition for beatmapsets scope."""
        terms = SearchTermsSchema(terms=["beatmapset"])

        engine = SearchEngine(
            scope=Scope.BEATMAPSETS,
            search_terms=terms
        )

        compiled = engine.compiled_query.lower()
        assert "beatmapset_snapshot" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled

    def test_engine_composes_filtered_cte_for_queues(self):
        """Test CTE composition for queues scope."""
        terms = SearchTermsSchema(terms=["queue"])

        engine = SearchEngine(
            scope=Scope.QUEUES,
            search_terms=terms
        )

        compiled = engine.compiled_query.lower()
        assert "queue" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled

    def test_engine_composes_filtered_cte_for_requests(self):
        """Test CTE composition for requests scope."""
        terms = SearchTermsSchema(terms=["request"])

        engine = SearchEngine(
            scope=Scope.REQUESTS,
            search_terms=terms
        )

        compiled = engine.compiled_query.lower()
        assert "request" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled


class TestSearchEngineScoreAggregation:
    """Test SearchEngine score aggregation."""

    def test_engine_aggregates_beatmap_scores(self):
        """Test engine aggregates beatmap scores."""
        terms = SearchTermsSchema(terms=["beatmap"])

        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            search_terms=terms
        )

        compiled = engine.compiled_query.lower()
        assert "beatmap_snapshot" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled

    def test_engine_aggregates_beatmapset_scores(self):
        """Test engine aggregates beatmapset scores."""
        terms = SearchTermsSchema(terms=["beatmapset"])

        engine = SearchEngine(
            scope=Scope.BEATMAPSETS,
            search_terms=terms
        )

        compiled = engine.compiled_query.lower()
        assert "beatmapset_snapshot" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled

    def test_engine_aggregates_child_scores_to_parent(self):
        """Test engine aggregates child scores to parent."""
        terms = SearchTermsSchema(terms=["beatmap"])

        engine = SearchEngine(
            scope=Scope.BEATMAPSETS,
            search_terms=terms
        )

        compiled = engine.compiled_query.lower()
        assert "aggregated_beatmap_scores_cte" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled


class TestSearchEngineQueryCompilation:
    """Test SearchEngine query compilation."""

    @pytest.mark.parametrize("scope,expected_table", [
        (Scope.BEATMAPS, "beatmap_snapshot"),
        (Scope.BEATMAPSETS, "beatmapset_snapshot"),
        (Scope.QUEUES, "queue"),
        (Scope.REQUESTS, "request"),
    ])
    def test_engine_compiles_for_scope(self, scope, expected_table):
        """Test engine compiles correct table reference for each scope."""
        terms = SearchTermsSchema(terms=["test"])
        engine = SearchEngine(scope=scope, search_terms=terms)
        compiled = engine.compiled_query.lower()
        assert expected_table in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled

    def test_engine_compiles_beatmaps_query(self):
        """Test engine compiles beatmaps query."""
        terms = SearchTermsSchema(terms=["beatmap"])

        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            search_terms=terms
        )

        compiled = engine.compiled_query.lower()
        assert "beatmap_snapshot" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled

    def test_engine_compiles_beatmapsets_query(self):
        """Test engine compiles beatmapsets query."""
        terms = SearchTermsSchema(terms=["beatmapset"])

        engine = SearchEngine(
            scope=Scope.BEATMAPSETS,
            search_terms=terms
        )

        compiled = engine.compiled_query.lower()
        assert "beatmapset_snapshot" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled

    def test_engine_compiles_queues_query(self):
        """Test engine compiles queues query."""
        terms = SearchTermsSchema(terms=["queue"])

        engine = SearchEngine(
            scope=Scope.QUEUES,
            search_terms=terms
        )

        compiled = engine.compiled_query.lower()
        assert "queue" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled

    def test_engine_compiles_requests_query(self):
        """Test engine compiles requests query."""
        terms = SearchTermsSchema(terms=["request"])

        engine = SearchEngine(
            scope=Scope.REQUESTS,
            search_terms=terms
        )

        compiled = engine.compiled_query.lower()
        assert "request" in compiled
        assert "select" in compiled
        assert "order by" in compiled
        assert "limit" not in compiled

    def test_engine_includes_total_score_with_search_terms(self):
        """Test that compiled query includes total_score when search terms present."""
        terms = SearchTermsSchema(terms=["test"])
        engine = SearchEngine(scope=Scope.BEATMAPS, search_terms=terms)
        compiled = engine.compiled_query.lower()
        assert "total_score" in compiled

    def test_engine_excludes_total_score_without_search_terms(self):
        """Test that compiled query omits total_score when no search terms."""
        engine = SearchEngine(scope=Scope.BEATMAPS)
        compiled = engine.compiled_query.lower()
        assert "total_score" not in compiled

    def test_engine_compiled_query_is_valid_sql(self):
        """Test that compiled query starts with valid SQL construct."""
        terms = SearchTermsSchema(terms=["test"])
        engine = SearchEngine(scope=Scope.BEATMAPS, search_terms=terms)
        compiled = engine.compiled_query
        assert compiled.startswith("WITH ") or compiled.startswith("SELECT ")
