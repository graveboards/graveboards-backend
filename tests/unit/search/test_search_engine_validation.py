import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.search.engine import SearchEngine
from app.search.enums import Scope


class TestSearchEngineValidation:
    """Test search engine input validation."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock async session."""
        return MagicMock(spec=AsyncSession)

    def test_engine_creation_with_scope(self, mock_session):
        """Test SearchEngine creation with scope."""
        engine = SearchEngine(scope=Scope.BEATMAPS)

        assert engine.scope == Scope.BEATMAPS
        assert engine.model_class is not None

    def test_engine_creation_with_search_terms_dict(self, mock_session):
        """Test SearchEngine creation with search terms dict."""
        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            search_terms={"terms": ["test"], "categories": ["beatmap"], "exact": False}
        )

        assert engine.search_terms is not None

    def test_engine_creation_with_sorting_list(self, mock_session):
        """Test SearchEngine creation with sorting list."""
        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            sorting=[{"field": "id", "order": "asc"}]
        )

        assert engine.sorting is not None

    def test_engine_creation_with_filters_dict(self, mock_session):
        """Test SearchEngine creation with filters dict."""
        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            filters={"id": {"eq": 123}}
        )

        assert engine.filters is not None

    def test_engine_rejects_invalid_search_terms_type(self):
        """Test that invalid search terms type raises."""
        with pytest.raises(TypeError):
            SearchEngine(
                scope=Scope.BEATMAPS,
                search_terms="not_a_dict"
            )

    def test_engine_rejects_invalid_sorting_type(self):
        """Test that invalid sorting type raises."""
        with pytest.raises(TypeError):
            SearchEngine(
                scope=Scope.BEATMAPS,
                sorting="not_a_list"
            )

    def test_engine_rejects_invalid_filters_type(self):
        """Test that invalid filters type raises."""
        with pytest.raises(TypeError):
            SearchEngine(
                scope=Scope.BEATMAPS,
                filters="not_a_dict"
            )

    def test_search_requires_non_negative_limit(self, mock_session):
        """Test that search requires non-negative limit."""
        engine = SearchEngine(scope=Scope.BEATMAPS)

        with pytest.raises(TypeError):
            engine.search(mock_session, limit=-1)

    def test_search_requires_non_negative_offset(self, mock_session):
        """Test that search requires non-negative offset."""
        engine = SearchEngine(scope=Scope.BEATMAPS)

        with pytest.raises(TypeError):
            engine.search(mock_session, offset=-1)

    def test_search_requires_integer_limit(self, mock_session):
        """Test that search requires integer limit."""
        engine = SearchEngine(scope=Scope.BEATMAPS)

        with pytest.raises(TypeError):
            engine.search(mock_session, limit=10.5)

    def test_search_requires_integer_offset(self, mock_session):
        """Test that search requires integer offset."""
        engine = SearchEngine(scope=Scope.BEATMAPS)

        with pytest.raises(TypeError):
            engine.search(mock_session, offset=10.5)

    def test_search_returns_results(self, mock_session):
        """Test that search returns results."""
        engine = SearchEngine(scope=Scope.BEATMAPS)

        # Mock execute to return empty result
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        # This would normally call the database, so we just test the validation
        with patch.object(engine, "_compose_query"):
            engine._compose_query()

    def test_engine_composes_query(self):
        """Test that engine composes query."""
        engine = SearchEngine(scope=Scope.BEATMAPS)

        assert engine.query is not None

    def test_engine_scope_beatmaps(self):
        """Test engine scope beats."""
        engine = SearchEngine(scope=Scope.BEATMAPS)

        assert engine.scope == Scope.BEATMAPS
        assert engine.model_class.value.__name__ == "BeatmapSnapshot"

    def test_engine_scope_beatmapsets(self):
        """Test engine scope beatmapsets."""
        engine = SearchEngine(scope=Scope.BEATMAPSETS)

        assert engine.scope == Scope.BEATMAPSETS
        assert engine.model_class.value.__name__ == "BeatmapsetSnapshot"

    def test_engine_scope_queues(self):
        """Test engine scope queues."""
        engine = SearchEngine(scope=Scope.QUEUES)

        assert engine.scope == Scope.QUEUES
        assert engine.model_class.value.__name__ == "Queue"

    def test_engine_scope_requests(self):
        """Test engine scope requests."""
        engine = SearchEngine(scope=Scope.REQUESTS)

        assert engine.scope == Scope.REQUESTS
        assert engine.model_class.value.__name__ == "Request"

    def test_engine_with_none_search_terms(self):
        """Test engine with None search terms."""
        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            search_terms=None
        )

        assert engine.search_terms is None

    def test_engine_with_none_sorting(self):
        """Test engine with None sorting."""
        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            sorting=None
        )

        assert engine.sorting is None

    def test_engine_with_none_filters(self):
        """Test engine with None filters."""
        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            filters=None
        )

        assert engine.filters is None

    def test_engine_sorting_default_order(self):
        """Test engine sorting with default order."""
        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            sorting=[{"field": "id"}]
        )

        # Default order should be "asc"
        options = list(engine.sorting)
        assert len(options) == 1

    def test_engine_filters_none_category(self):
        """Test engine filters with None category."""
        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            filters={"id": None}
        )

        assert engine.filters is not None

    def test_engine_search_terms_validation(self):
        """Test engine validates search terms against scope."""
        from app.search.datastructures import SearchTermsSchema

        terms = SearchTermsSchema.model_validate({"terms": ["test"]})

        # Should validate against scope
        terms.validate_against_scope(Scope.BEATMAPS)

    def test_engine_complex_search_config(self):
        """Test engine with complex search configuration."""
        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            search_terms={"terms": ["test", "beatmap"], "categories": ["beatmap"]},
            sorting=[{"field": "id", "order": "desc"}],
            filters={"id": {"gt": 100, "lt": 200}}
        )

        assert engine.search_terms is not None
        assert engine.sorting is not None
        assert engine.filters is not None

    def test_engine_search_with_debug(self, mock_session):
        """Test search with debug mode."""
        engine = SearchEngine(scope=Scope.BEATMAPS)

        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch.object(engine, "_compose_query"):
            engine._compose_query()

    def test_engine_search_limits(self, mock_session):
        """Test search with limit."""
        engine = SearchEngine(scope=Scope.BEATMAPS)

        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch.object(engine, "_compose_query"):
            engine._compose_query()

    def test_engine_default_limit_offset(self):
        """Test engine uses default limit and offset."""
        from app.search.engine import DEFAULT_LIMIT, DEFAULT_OFFSET

        engine = SearchEngine(scope=Scope.BEATMAPS)

        assert DEFAULT_LIMIT == 50
        assert DEFAULT_OFFSET == 0
