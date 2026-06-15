import pytest
from sqlalchemy.sql import select
from sqlalchemy.sql.selectable import CTE, Select
from sqlalchemy.orm import aliased

from app.database.ctes.utils import extract_cte_target_scalar
from app.database.models import ModelClass, BeatmapSnapshot


class TestCTEUtils:
    """Test CTE utility functions."""

    def test_extract_cte_target_scalar_basic(self):
        """Test basic CTE target scalar extraction."""
        stmt: Select = select(
            BeatmapSnapshot.id.label("id"),
            BeatmapSnapshot.beatmap_id.label("target")
        ).cte("test_cte")
        result = extract_cte_target_scalar(stmt, ModelClass.BEATMAP_SNAPSHOT)
        
        assert result is not None

    def test_extract_cte_target_scalar_with_alias(self):
        """Test CTE target scalar extraction with alias."""
        stmt: Select = select(
            BeatmapSnapshot.id.label("id"),
            BeatmapSnapshot.beatmap_id.label("target")
        ).cte("test_cte")
        result = extract_cte_target_scalar(stmt, ModelClass.BEATMAP_SNAPSHOT, use_alias=True)
        
        assert result is not None

    def test_extract_cte_target_scalar_custom_id_label(self):
        """Test CTE target scalar extraction with custom ID label."""
        stmt: Select = select(
            BeatmapSnapshot.id.label("beatmap_id"),
            BeatmapSnapshot.beatmap_id.label("target")
        ).cte("test_cte")
        result = extract_cte_target_scalar(stmt, ModelClass.BEATMAP_SNAPSHOT, id_column_label="beatmap_id")
        
        assert result is not None
