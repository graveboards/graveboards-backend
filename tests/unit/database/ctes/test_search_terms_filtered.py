import pytest
from sqlalchemy.sql import select

from app.search.datastructures import SearchTermsSchema
from app.search.enums import Scope, SearchableFieldCategory
from app.database.ctes.search_terms_filtered import (
    search_terms_filtered_cte_factory,
    get_filter_stmt,
    build_search_terms_filtered_cte
)


class TestSearchTermsFilteredCTE:
    """Test search terms filtering CTE."""

    def test_search_terms_filtered_cte_factory_single_term(self):
        """Test CTE factory with single search term."""
        terms = SearchTermsSchema(terms=["beatmap"])
        
        cte = search_terms_filtered_cte_factory(Scope.BEATMAPS, terms)
        
        assert cte is not None

    def test_search_terms_filtered_cte_factory_multiple_terms(self):
        """Test CTE factory with multiple search terms."""
        terms = SearchTermsSchema(terms=["beatmap", "osu"])
        
        cte = search_terms_filtered_cte_factory(Scope.BEATMAPS, terms)
        
        assert cte is not None

    def test_search_terms_filtered_cte_factory_case_insensitive(self):
        """Test CTE factory with case insensitive search."""
        terms = SearchTermsSchema(terms=["beatmap"], case_sensitive=False)
        
        cte = search_terms_filtered_cte_factory(Scope.BEATMAPS, terms)
        
        assert cte is not None

    def test_search_terms_filtered_cte_factory_beatmapsets_scope(self):
        """Test CTE factory with beatmapsets scope."""
        terms = SearchTermsSchema(terms=["beatmapset"])
        
        cte = search_terms_filtered_cte_factory(Scope.BEATMAPSETS, terms)
        
        assert cte is not None

    def test_search_terms_filtered_cte_factory_queues_scope(self):
        """Test CTE factory with queues scope."""
        terms = SearchTermsSchema(terms=["queue"])
        
        cte = search_terms_filtered_cte_factory(Scope.QUEUES, terms)
        
        assert cte is not None

    def test_search_terms_filtered_cte_factory_requests_scope(self):
        """Test CTE factory with requests scope."""
        terms = SearchTermsSchema(terms=["request"])
        
        cte = search_terms_filtered_cte_factory(Scope.REQUESTS, terms)
        
        assert cte is not None

    def test_build_search_terms_filtered_cte_alias(self):
        """Test build_search_terms_filtered_cte is alias."""
        assert build_search_terms_filtered_cte is search_terms_filtered_cte_factory


class TestGetFilterStmt:
    """Test get_filter_stmt function."""

    def test_get_filter_stmt_beatmaps_beatmap(self):
        """Test filter stmt for beatmaps scope with beatmap category."""
        from app.database.models import BeatmapSnapshot
        
        stmt = get_filter_stmt(
            scope=Scope.BEATMAPS,
            category=SearchableFieldCategory.BEATMAP,
            target=BeatmapSnapshot.version,
            like_operator="ilike",
            pattern="%test%"
        )
        
        assert stmt is not None

    def test_get_filter_stmt_beatmaps_beatmapset(self):
        """Test filter stmt for beatmaps scope with beatmapset category."""
        from app.database.models import BeatmapSnapshot, BeatmapsetSnapshot
        from app.database.models import beatmap_snapshot_beatmapset_snapshot_association
        
        stmt = get_filter_stmt(
            scope=Scope.BEATMAPS,
            category=SearchableFieldCategory.BEATMAPSET,
            target=BeatmapsetSnapshot.title,
            like_operator="ilike",
            pattern="%test%"
        )
        
        assert stmt is not None

    def test_get_filter_stmt_beatmapsets_beatmap(self):
        """Test filter stmt for beatmapsets scope with beatmap category."""
        from app.database.models import BeatmapSnapshot, BeatmapsetSnapshot
        from app.database.models import beatmap_snapshot_beatmapset_snapshot_association
        
        stmt = get_filter_stmt(
            scope=Scope.BEATMAPSETS,
            category=SearchableFieldCategory.BEATMAP,
            target=BeatmapSnapshot.version,
            like_operator="ilike",
            pattern="%test%"
        )
        
        assert stmt is not None

    def test_get_filter_stmt_beatmapsets_beatmapset(self):
        """Test filter stmt for beatmapsets scope with beatmapset category."""
        from app.database.models import BeatmapsetSnapshot
        
        stmt = get_filter_stmt(
            scope=Scope.BEATMAPSETS,
            category=SearchableFieldCategory.BEATMAPSET,
            target=BeatmapsetSnapshot.title,
            like_operator="ilike",
            pattern="%test%"
        )
        
        assert stmt is not None

    def test_get_filter_stmt_queues_beatmap(self):
        """Test filter stmt for queues scope with beatmap category."""
        from app.database.models import Queue
        
        stmt = get_filter_stmt(
            scope=Scope.QUEUES,
            category=SearchableFieldCategory.BEATMAP,
            target=Queue.name,
            like_operator="ilike",
            pattern="%test%"
        )
        
        assert stmt is not None

    def test_get_filter_stmt_queues_beatmapset(self):
        """Test filter stmt for queues scope with beatmapset category."""
        from app.database.models import Queue
        
        stmt = get_filter_stmt(
            scope=Scope.QUEUES,
            category=SearchableFieldCategory.BEATMAPSET,
            target=Queue.name,
            like_operator="ilike",
            pattern="%test%"
        )
        
        assert stmt is not None

    def test_get_filter_stmt_queues_queue(self):
        """Test filter stmt for queues scope with queue category."""
        from app.database.models import Queue
        
        stmt = get_filter_stmt(
            scope=Scope.QUEUES,
            category=SearchableFieldCategory.QUEUE,
            target=Queue.name,
            like_operator="ilike",
            pattern="%test%"
        )
        
        assert stmt is not None

    def test_get_filter_stmt_queues_request(self):
        """Test filter stmt for queues scope with request category."""
        from app.database.models import Queue
        
        stmt = get_filter_stmt(
            scope=Scope.QUEUES,
            category=SearchableFieldCategory.REQUEST,
            target=Queue.name,
            like_operator="ilike",
            pattern="%test%"
        )
        
        assert stmt is not None

    def test_get_filter_stmt_requests_beatmap(self):
        """Test filter stmt for requests scope with beatmap category."""
        from app.database.models import Request
        
        stmt = get_filter_stmt(
            scope=Scope.REQUESTS,
            category=SearchableFieldCategory.BEATMAP,
            target=Request.comment,
            like_operator="ilike",
            pattern="%test%"
        )
        
        assert stmt is not None

    def test_get_filter_stmt_requests_beatmapset(self):
        """Test filter stmt for requests scope with beatmapset category."""
        from app.database.models import Request
        
        stmt = get_filter_stmt(
            scope=Scope.REQUESTS,
            category=SearchableFieldCategory.BEATMAPSET,
            target=Request.comment,
            like_operator="ilike",
            pattern="%test%"
        )
        
        assert stmt is not None

    def test_get_filter_stmt_requests_request(self):
        """Test filter stmt for requests scope with request category."""
        from app.database.models import Request
        
        stmt = get_filter_stmt(
            scope=Scope.REQUESTS,
            category=SearchableFieldCategory.REQUEST,
            target=Request.comment,
            like_operator="ilike",
            pattern="%test%"
        )
        
        assert stmt is not None

    def test_get_filter_stmt_unsupported_category_raises(self):
        """Test that unsupported category raises."""
        from app.database.models import Queue
        
        with pytest.raises(ValueError):
            get_filter_stmt(
                scope=Scope.QUEUES,
                category=SearchableFieldCategory.PROFILE,
                target=Queue.name,
                like_operator="ilike",
                pattern="%test%"
            )

    def test_get_filter_stmt_unsupported_scope_raises(self):
        """Test that unsupported scope raises."""
        from app.database.models import BeatmapSnapshot
        
        with pytest.raises(ValueError):
            get_filter_stmt(
                scope=Scope.SCORES,
                category=SearchableFieldCategory.BEATMAP,
                target=BeatmapSnapshot.version,
                like_operator="ilike",
                pattern="%test%"
            )
