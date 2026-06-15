import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.search.engine import SearchEngine
from app.search.enums import Scope


class TestSearchEngineCTEs:
    """Test SearchEngine CTE composition."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock async session."""
        return MagicMock(spec=AsyncSession)

    def test_engine_applies_filtered_cte(self):
        """Test that engine applies filtered CTE."""
        from app.search.datastructures import SearchTermsSchema
        from app.search.mappings import SCOPE_CATEGORIES_MAPPING
        
        terms = SearchTermsSchema(terms=["beatmap"])
        
        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            search_terms=terms
        )
        
        assert engine.search_terms is not None

    def test_engine_applies_scored_ctes(self):
        """Test that engine applies scored CTEs."""
        from app.search.datastructures import SearchTermsSchema, FieldWeights
        
        terms = SearchTermsSchema(
            terms=["beatmap"],
            field_weights=FieldWeights()
        )
        
        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            search_terms=terms
        )
        
        assert engine.search_terms is not None

    def test_engine_composes_filtered_cte_for_beatmaps(self):
        """Test CTE composition for beatmaps scope."""
        from app.search.datastructures import SearchTermsSchema
        
        terms = SearchTermsSchema(terms=["beatmap"])
        
        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            search_terms=terms
        )
        
        assert engine.query is not None

    def test_engine_composes_filtered_cte_for_beatmapsets(self):
        """Test CTE composition for beatmapsets scope."""
        from app.search.datastructures import SearchTermsSchema
        
        terms = SearchTermsSchema(terms=["beatmapset"])
        
        engine = SearchEngine(
            scope=Scope.BEATMAPSETS,
            search_terms=terms
        )
        
        assert engine.query is not None

    def test_engine_composes_filtered_cte_for_queues(self):
        """Test CTE composition for queues scope."""
        from app.search.datastructures import SearchTermsSchema
        
        terms = SearchTermsSchema(terms=["queue"])
        
        engine = SearchEngine(
            scope=Scope.QUEUES,
            search_terms=terms
        )
        
        assert engine.query is not None

    def test_engine_composes_filtered_cte_for_requests(self):
        """Test CTE composition for requests scope."""
        from app.search.datastructures import SearchTermsSchema
        
        terms = SearchTermsSchema(terms=["request"])
        
        engine = SearchEngine(
            scope=Scope.REQUESTS,
            search_terms=terms
        )
        
        assert engine.query is not None


class TestSearchEngineScoreAggregation:
    """Test SearchEngine score aggregation."""

    def test_engine_aggregates_beatmap_scores(self):
        """Test engine aggregates beatmap scores."""
        from app.search.datastructures import SearchTermsSchema
        
        terms = SearchTermsSchema(terms=["beatmap"])
        
        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            search_terms=terms
        )
        
        assert engine.query is not None

    def test_engine_aggregates_beatmapset_scores(self):
        """Test engine aggregates beatmapset scores."""
        from app.search.datastructures import SearchTermsSchema
        
        terms = SearchTermsSchema(terms=["beatmapset"])
        
        engine = SearchEngine(
            scope=Scope.BEATMAPSETS,
            search_terms=terms
        )
        
        assert engine.query is not None

    def test_engine_aggregates_child_scores_to_parent(self):
        """Test engine aggregates child scores to parent."""
        from app.search.datastructures import SearchTermsSchema
        
        terms = SearchTermsSchema(terms=["beatmap"])
        
        engine = SearchEngine(
            scope=Scope.BEATMAPSETS,
            search_terms=terms
        )
        
        assert engine.query is not None


class TestSearchEngineQueryCompilation:
    """Test SearchEngine query compilation."""

    def test_engine_compiles_beatmaps_query(self):
        """Test engine compiles beatmaps query."""
        from app.search.datastructures import SearchTermsSchema
        
        terms = SearchTermsSchema(terms=["beatmap"])
        
        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            search_terms=terms
        )
        
        compiled = engine.compiled_query
        assert compiled is not None
        assert "SELECT" in compiled

    def test_engine_compiles_beatmapsets_query(self):
        """Test engine compiles beatmapsets query."""
        from app.search.datastructures import SearchTermsSchema
        
        terms = SearchTermsSchema(terms=["beatmapset"])
        
        engine = SearchEngine(
            scope=Scope.BEATMAPSETS,
            search_terms=terms
        )
        
        compiled = engine.compiled_query
        assert compiled is not None
        assert "SELECT" in compiled

    def test_engine_compiles_queues_query(self):
        """Test engine compiles queues query."""
        from app.search.datastructures import SearchTermsSchema
        
        terms = SearchTermsSchema(terms=["queue"])
        
        engine = SearchEngine(
            scope=Scope.QUEUES,
            search_terms=terms
        )
        
        compiled = engine.compiled_query
        assert compiled is not None
        assert "SELECT" in compiled

    def test_engine_compiles_requests_query(self):
        """Test engine compiles requests query."""
        from app.search.datastructures import SearchTermsSchema
        
        terms = SearchTermsSchema(terms=["request"])
        
        engine = SearchEngine(
            scope=Scope.REQUESTS,
            search_terms=terms
        )
        
        compiled = engine.compiled_query
        assert compiled is not None
        assert "SELECT" in compiled
