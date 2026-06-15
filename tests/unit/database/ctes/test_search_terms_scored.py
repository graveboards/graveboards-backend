import pytest
from unittest.mock import patch, MagicMock

from app.search.datastructures import SearchTermsSchema, FieldWeights, PatternMultipliers
from app.search.enums import Scope, SearchableFieldCategory
from app.database.ctes.search_terms_scored import (
    search_terms_scored_ctes_factory,
    _generate_term_score_stmts,
    _process_field_groups,
    aggregated_child_scores_to_parent_cte_factory
)


class TestSearchTermsScoredCTE:
    """Test search terms scoring CTE."""

    @pytest.fixture
    def mock_search_terms(self):
        """Create mock search terms."""
        return SearchTermsSchema(
            terms=["beatmap"],
            case_sensitive=False,
            field_weights=FieldWeights()
        )

    @pytest.fixture
    def mock_multipliers(self):
        """Create mock multipliers."""
        return PatternMultipliers()

    def test_search_terms_scored_ctes_factory_beatmaps(self, mock_search_terms):
        """Test scoring CTE factory for beatmaps scope."""
        ctes = search_terms_scored_ctes_factory(Scope.BEATMAPS, mock_search_terms)
        
        assert isinstance(ctes, dict)
        assert len(ctes) > 0

    def test_search_terms_scored_ctes_factory_beatmapsets(self, mock_search_terms):
        """Test scoring CTE factory for beatmapsets scope."""
        ctes = search_terms_scored_ctes_factory(Scope.BEATMAPSETS, mock_search_terms)
        
        assert isinstance(ctes, dict)
        assert len(ctes) > 0

    def test_search_terms_scored_ctes_factory_queues(self, mock_search_terms):
        """Test scoring CTE factory for queues scope."""
        ctes = search_terms_scored_ctes_factory(Scope.QUEUES, mock_search_terms)
        
        assert isinstance(ctes, dict)
        assert len(ctes) > 0

    def test_search_terms_scored_ctes_factory_requests(self, mock_search_terms):
        """Test scoring CTE factory for requests scope."""
        ctes = search_terms_scored_ctes_factory(Scope.REQUESTS, mock_search_terms)
        
        assert isinstance(ctes, dict)
        assert len(ctes) > 0

    def test_search_terms_scored_ctes_factory_multiple_terms(self):
        """Test scoring CTE factory with multiple terms."""
        terms = SearchTermsSchema(
            terms=["beatmap", "osu"],
            case_sensitive=False,
            field_weights=FieldWeights()
        )
        
        ctes = search_terms_scored_ctes_factory(Scope.BEATMAPS, terms)
        
        assert isinstance(ctes, dict)
        assert len(ctes) > 0

    def test_search_terms_scored_ctes_factory_case_sensitive(self):
        """Test scoring CTE factory with case sensitive search."""
        terms = SearchTermsSchema(
            terms=["beatmap"],
            case_sensitive=True,
            field_weights=FieldWeights()
        )
        
        ctes = search_terms_scored_ctes_factory(Scope.BEATMAPS, terms)
        
        assert isinstance(ctes, dict)
        assert len(ctes) > 0


class TestGenerateTermScoreStmts:
    """Test _generate_term_score_stmts function."""

    def test_generate_term_score_stmts_yields_statements(self):
        """Test that generator yields SELECT statements."""
        terms = SearchTermsSchema(
            terms=["beatmap"],
            case_sensitive=False,
            field_weights=FieldWeights()
        )
        
        stmts = list(_generate_term_score_stmts(Scope.BEATMAPS, terms))
        
        assert len(stmts) > 0
        for category, stmt in stmts:
            assert category is not None
            assert stmt is not None


class TestProcessFieldGroups:
    """Test _process_field_groups function."""

    def test_process_field_groups_no_groups(self):
        """Test processing with no field groups."""
        from sqlalchemy.sql import union_all, select, literal
        
        base_query = union_all(
            select(literal(1).label("id"), literal("field").label("field")),
            select(literal(2).label("id"), literal("field").label("field"))
        )
        
        result = _process_field_groups(base_query, SearchableFieldCategory.BEATMAP, {})
        
        assert result is not None

    def test_process_field_groups_with_groups(self):
        """Test processing with field groups."""
        from sqlalchemy.sql import union_all, select, literal
        
        base_query = union_all(
            select(literal(1).label("id"), literal("title").label("field"), literal("term").label("term"), literal("pattern").label("pattern"), literal(10).label("score")),
            select(literal(2).label("id"), literal("title_unicode").label("field"), literal("term").label("term"), literal("pattern").label("pattern"), literal(15).label("score"))
        ).subquery()
        
        field_groups_config = {
            SearchableFieldCategory.BEATMAPSET: {
                "title": {"title", "title_unicode"}
            }
        }
        
        result = _process_field_groups(
            base_query,
            SearchableFieldCategory.BEATMAPSET,
            field_groups_config
        )
        
        assert result is not None


class TestAggregatedChildScoresToParentCTE:
    """Test aggregated_child_scores_to_parent_cte_factory function."""

    def test_aggregated_child_scores_basic(self):
        """Test basic child to parent aggregation."""
        from sqlalchemy.sql import select, literal, func
        from app.database.models import (
            BeatmapSnapshot,
            BeatmapsetSnapshot,
            beatmap_snapshot_beatmapset_snapshot_association
        )
        
        child_score_cte = (
            select(
                literal(1).label("id"),
                func.jsonb_build_object(
                    "field", literal("version"),
                    "term", literal("beatmap"),
                    "pattern", literal("%beatmap%"),
                    "score", literal(10)
                ).label("score_details")
            )
            .cte("child_score_cte")
        )
        
        result = aggregated_child_scores_to_parent_cte_factory(
            child_score_cte=child_score_cte,
            mapping_table=beatmap_snapshot_beatmapset_snapshot_association,
            mapping_child_fk="beatmap_snapshot_id",
            mapping_parent_fk="beatmapset_snapshot_id",
            cte_name="parent_score_cte"
        )
        
        assert result is not None
