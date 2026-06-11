"""
Integration tests for POST /api/v1/beatmapsets endpoint (admin-only).

Tests the beatmap archival functionality.
"""
import pytest

from unittest.mock import AsyncMock, MagicMock


class TestBeatmapsetsPostEndpoint:
    """Integration tests for POST /api/v1/beatmapsets admin endpoint."""

    TEST_BEATMAPSET_ID = 35965

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_post_beatmapsets_admin_creates_snapshot(self):
        """Test successful beatmap archival by admin user."""
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
        assert "snapshotted_beatmapset" in result[0]
        assert "snapshotted_beatmaps" in result[0]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_post_beatmapsets_admin_updates(self):
        """Test successful beatmap update by admin user."""
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
        assert "updated_beatmapset" in result[0]
        assert "updated_beatmaps" in result[0]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_post_beatmapsets_admin_up_to_date(self):
        """Test beatmapset that is fully up-to-date."""
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

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_post_beatmapsets_osu_api_error(self):
        """Test that osu! API errors are properly handled."""
        import httpx
        from unittest.mock import MagicMock
        
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
