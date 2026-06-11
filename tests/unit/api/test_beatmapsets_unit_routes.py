"""
Unit tests for POST /api/v1/beatmapsets endpoint (admin-only).

Tests the beatmap archival logic with mocked dependencies (fast, isolated).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestBeatmapsetsPostUnit:
    """Unit tests for POST /api/v1/beatmapsets endpoint."""

    TEST_BEATMAPSET_ID = 35965

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_admin_archival_creates_snapshot(self):
        """Test that admin can create beatmapset snapshot."""
        mock_rc = AsyncMock()
        mock_db = AsyncMock()
        
        mock_bm = MagicMock()
        mock_bm.archive = AsyncMock(return_value={
            "message": "Snapshotted 1 beatmap(s)",
            "updated_beatmapset": None,
            "updated_beatmaps": [],
            "snapshotted_beatmapset": {"id": 1, "beatmapset_id": self.TEST_BEATMAPSET_ID, "snapshot_number": 1, "checksum": "abc"},
            "snapshotted_beatmaps": [{"id": 1, "beatmap_id": 116383, "snapshot_number": 1, "checksum": "abc"}],
        })
        
        from api.v1.beatmapsets import post
        
        result = await post(
            body={"id": self.TEST_BEATMAPSET_ID},
            rc=mock_rc,
            db=mock_db,
            bm=mock_bm,
        )
        
        assert result[1] == 201
        assert result[0]["message"] == "Snapshotted 1 beatmap(s)"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_admin_archival_updates_existing(self):
        """Test that admin can update existing beatmapset."""
        mock_rc = AsyncMock()
        mock_db = AsyncMock()
        
        mock_bm = MagicMock()
        mock_bm.archive = AsyncMock(return_value={
            "message": "Updated 2 field(s) in the beatmapset and 1 field(s) in 1 beatmap(s)",
            "updated_beatmapset": {"beatmapset_id": self.TEST_BEATMAPSET_ID, "bpm": 130.0, "title": "New Title"},
            "updated_beatmaps": [{"beatmap_id": 116383, "version": "Hard"}],
            "snapshotted_beatmapset": None,
            "snapshotted_beatmaps": [],
        })
        
        from api.v1.beatmapsets import post
        
        result = await post(
            body={"id": self.TEST_BEATMAPSET_ID},
            rc=mock_rc,
            db=mock_db,
            bm=mock_bm,
        )
        
        assert result[1] == 200
        assert result[0]["message"] == "Updated 2 field(s) in the beatmapset and 1 field(s) in 1 beatmap(s)"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_admin_archival_up_to_date(self):
        """Test that up-to-date beatmapset returns 200 with message."""
        mock_rc = AsyncMock()
        mock_db = AsyncMock()
        
        mock_bm = MagicMock()
        mock_bm.archive = AsyncMock(return_value={
            "message": "The beatmapset and its beatmaps are fully up-to-date",
            "updated_beatmapset": None,
            "updated_beatmaps": [],
            "snapshotted_beatmapset": None,
            "snapshotted_beatmaps": [],
        })
        
        from api.v1.beatmapsets import post
        
        result = await post(
            body={"id": self.TEST_BEATMAPSET_ID},
            rc=mock_rc,
            db=mock_db,
            bm=mock_bm,
        )
        
        assert result[1] == 200
        assert result[0]["message"] == "The beatmapset and its beatmaps are fully up-to-date"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_osu_api_error_handling(self):
        """Test that osu! API errors are properly handled."""
        import httpx
        
        mock_rc = AsyncMock()
        mock_db = AsyncMock()
        
        mock_bm = MagicMock()
        mock_bm.archive = AsyncMock(side_effect=httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=MagicMock(status_code=404, json=lambda: {"error": "Beatmapset not found"}),
        ))
        
        from api.v1.beatmapsets import post
        
        result = await post(
            body={"id": self.TEST_BEATMAPSET_ID},
            rc=mock_rc,
            db=mock_db,
            bm=mock_bm,
        )
        
        assert result[1] == 404
        assert "error" in result[0]
