"""
Integration tests for POST /api/v1/beatmapsets endpoint (admin-only).

Tests the beatmap archival via full HTTP stack with mocked dependencies.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestBeatmapsetsPostIntegration:
    """Integration tests for POST /api/v1/beatmapsets admin endpoint."""

    TEST_BEATMAPSET_ID = 35965

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_disabled_security(self, TestClient):
        """Test beatmap archival works with DISABLE_SECURITY=True (integration)."""
        from unittest.mock import AsyncMock, MagicMock, patch
        
        mock_rc = AsyncMock()
        mock_rc.hgetall = AsyncMock(return_value=None)
        mock_rc.getdel = AsyncMock(return_value=None)
        
        mock_bm = MagicMock()
        mock_bm.archive = AsyncMock(return_value={
            "message": "Snapshotted 1 beatmap(s)",
            "updated_beatmapset": None,
            "updated_beatmaps": [],
            "snapshotted_beatmapset": {"id": 1, "beatmapset_id": self.TEST_BEATMAPSET_ID, "snapshot_number": 1, "checksum": "abc"},
            "snapshotted_beatmaps": [{"id": 1, "beatmap_id": 116383, "snapshot_number": 1, "checksum": "abc"}],
        })
        
        with patch('api.v1.beatmapsets.BeatmapManager', return_value=mock_bm), \
             patch('app.beatmaps.BeatmapManager', return_value=mock_bm), \
             patch('app.osu_api.OsuAPIClient') as mock_osu_client:
            mock_osu_client.return_value.rc = mock_rc
            body = {"id": self.TEST_BEATMAPSET_ID}
            response = TestClient.post("/api/v1/beatmapsets", json=body)
        
        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert "Snapshotted" in data["message"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_with_update(self, TestClient):
        """Test beatmap archival that updates existing data (integration)."""
        mock_rc = AsyncMock()
        mock_rc.hgetall = AsyncMock(return_value=None)
        mock_rc.getdel = AsyncMock(return_value=None)
        
        mock_bm = MagicMock()
        mock_bm.archive = AsyncMock(return_value={
            "message": "Updated 2 field(s) in the beatmapset and 1 field(s) in 1 beatmap(s)",
            "updated_beatmapset": {"beatmapset_id": self.TEST_BEATMAPSET_ID, "bpm": 130.0, "title": "New Title"},
            "updated_beatmaps": [{"beatmap_id": 116383, "version": "Hard"}],
            "snapshotted_beatmapset": None,
            "snapshotted_beatmaps": [],
        })
        
        with patch('api.v1.beatmapsets.BeatmapManager', return_value=mock_bm), \
             patch('app.beatmaps.BeatmapManager', return_value=mock_bm), \
             patch('app.osu_api.OsuAPIClient') as mock_osu_client:
            mock_osu_client.return_value.rc = mock_rc
            body = {"id": self.TEST_BEATMAPSET_ID}
            response = TestClient.post("/api/v1/beatmapsets", json=body)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Updated" in data["message"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_up_to_date(self, TestClient):
        """Test beatmap archival that detects up-to-date data (integration)."""
        mock_rc = AsyncMock()
        mock_rc.hgetall = AsyncMock(return_value=None)
        mock_rc.getdel = AsyncMock(return_value=None)
        
        mock_bm = MagicMock()
        mock_bm.archive = AsyncMock(return_value={
            "message": "The beatmapset and its beatmaps are fully up-to-date",
            "updated_beatmapset": None,
            "updated_beatmaps": [],
            "snapshotted_beatmapset": None,
            "snapshotted_beatmaps": [],
        })
        
        with patch('api.v1.beatmapsets.BeatmapManager', return_value=mock_bm), \
             patch('app.beatmaps.BeatmapManager', return_value=mock_bm), \
             patch('app.osu_api.OsuAPIClient') as mock_osu_client:
            mock_osu_client.return_value.rc = mock_rc
            body = {"id": self.TEST_BEATMAPSET_ID}
            response = TestClient.post("/api/v1/beatmapsets", json=body)
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "fully up-to-date" in data["message"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_osu_api_error_handling(self, TestClient):
        """Test that osu! API errors are properly handled (integration)."""
        import httpx
        from unittest.mock import MagicMock, patch
        
        mock_rc = AsyncMock()
        mock_rc.hgetall = AsyncMock(return_value=None)
        mock_rc.getdel = AsyncMock(return_value=None)
        
        mock_bm = MagicMock()
        mock_bm.archive = AsyncMock(side_effect=httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=MagicMock(status_code=404, json=lambda: {"error": "Beatmapset not found"}),
        ))
        
        with patch('api.v1.beatmapsets.BeatmapManager', return_value=mock_bm), \
             patch('app.beatmaps.BeatmapManager', return_value=mock_bm), \
             patch('app.osu_api.OsuAPIClient') as mock_osu_client:
            mock_osu_client.return_value.rc = mock_rc
            body = {"id": self.TEST_BEATMAPSET_ID}
            response = TestClient.post("/api/v1/beatmapsets", json=body)
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
