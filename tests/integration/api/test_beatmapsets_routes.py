"""
Integration tests for POST /api/v1/beatmapsets endpoint (admin-only).

Tests the beatmap archival via full HTTP stack.
"""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestBeatmapsetsPostIntegration:
    """Integration tests for POST /api/v1/beatmapsets admin endpoint."""

    TEST_BEATMAPSET_ID = 35965

    @pytest.fixture
    def mock_beatmap_manager(self):
        """Create a mock beatmap manager with proper archive behavior."""
        from unittest.mock import MagicMock, AsyncMock

        def create_manager(result):
            mock_bm = MagicMock()
            mock_bm.archive = AsyncMock(return_value=result)
            return mock_bm

        return create_manager

    @pytest.fixture
    def mock_rc(self):
        """Create a mock Redis client."""
        from unittest.mock import AsyncMock

        mock_rc = AsyncMock()
        mock_rc.hgetall = AsyncMock(return_value=None)
        mock_rc.getdel = AsyncMock(return_value=None)
        mock_rc.hset = AsyncMock(return_value=True)
        mock_rc.expire = AsyncMock(return_value=True)
        return mock_rc

    @pytest.fixture
    def mock_osu_client(self, mock_rc):
        """Create a mock osu client."""
        from unittest.mock import MagicMock

        mock_client = MagicMock()
        mock_client.rc = mock_rc
        return mock_client

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_archival_creates_snapshot(self, TestClient, mock_beatmap_manager, mock_osu_client):
        """Test successful beatmap archival that creates new snapshot."""
        mock_bm = mock_beatmap_manager({
            "message": "Snapshotted 1 beatmap(s)",
            "updated_beatmapset": None,
            "updated_beatmaps": [],
            "snapshotted_beatmapset": {"id": 1, "beatmapset_id": self.TEST_BEATMAPSET_ID, "snapshot_number": 1, "checksum": "abc"},
            "snapshotted_beatmaps": [{"id": 1, "beatmap_id": 116383, "snapshot_number": 1, "checksum": "abc"}],
        })

        with patch('api.v1.beatmapsets.BeatmapManager', return_value=mock_bm), \
             patch('app.beatmaps.BeatmapManager', return_value=mock_bm), \
             patch('app.osu_api.OsuAPIClient', return_value=mock_osu_client):
            body = {"id": self.TEST_BEATMAPSET_ID}
            response = TestClient.post("/api/v1/beatmapsets", json=body)

        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert "Snapshotted" in data["message"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_archival_updates_existing(self, TestClient, mock_beatmap_manager, mock_osu_client):
        """Test successful beatmap archival that updates existing data."""
        mock_bm = mock_beatmap_manager({
            "message": "Updated 2 field(s) in the beatmapset and 1 field(s) in 1 beatmap(s)",
            "updated_beatmapset": {"beatmapset_id": self.TEST_BEATMAPSET_ID, "bpm": 130.0, "title": "New Title"},
            "updated_beatmaps": [{"beatmap_id": 116383, "version": "Hard"}],
            "snapshotted_beatmapset": None,
            "snapshotted_beatmaps": [],
        })

        with patch('api.v1.beatmapsets.BeatmapManager', return_value=mock_bm), \
             patch('app.beatmaps.BeatmapManager', return_value=mock_bm), \
             patch('app.osu_api.OsuAPIClient', return_value=mock_osu_client):
            body = {"id": self.TEST_BEATMAPSET_ID}
            response = TestClient.post("/api/v1/beatmapsets", json=body)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Updated" in data["message"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_archival_up_to_date(self, TestClient, mock_beatmap_manager, mock_osu_client):
        """Test successful beatmap archival that detects up-to-date data."""
        mock_bm = mock_beatmap_manager({
            "message": "The beatmapset and its beatmaps are fully up-to-date",
            "updated_beatmapset": None,
            "updated_beatmaps": [],
            "snapshotted_beatmapset": None,
            "snapshotted_beatmaps": [],
        })

        with patch('api.v1.beatmapsets.BeatmapManager', return_value=mock_bm), \
             patch('app.beatmaps.BeatmapManager', return_value=mock_bm), \
             patch('app.osu_api.OsuAPIClient', return_value=mock_osu_client):
            body = {"id": self.TEST_BEATMAPSET_ID}
            response = TestClient.post("/api/v1/beatmapsets", json=body)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "fully up-to-date" in data["message"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_osu_api_error_handling(self, TestClient, mock_beatmap_manager, mock_osu_client):
        """Test that osu! API errors are properly handled."""
        import httpx
        from unittest.mock import MagicMock

        mock_bm = mock_beatmap_manager(None)
        mock_bm.archive = AsyncMock(side_effect=httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=MagicMock(status_code=404, json=lambda: {"error": "Beatmapset not found"}),
        ))

        with patch('api.v1.beatmapsets.BeatmapManager', return_value=mock_bm), \
             patch('app.beatmaps.BeatmapManager', return_value=mock_bm), \
             patch('app.osu_api.OsuAPIClient', return_value=mock_osu_client):
            body = {"id": self.TEST_BEATMAPSET_ID}
            response = TestClient.post("/api/v1/beatmapsets", json=body)

        assert response.status_code == 404
        data = response.json()
        assert "error" in data

    @pytest.mark.integration
    @pytest.mark.asyncio

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_success_with_auth(self, TestClient, mock_beatmap_manager, mock_osu_client, admin_user_token):
        """Test that admin user can successfully post beatmapset with valid token."""
        mock_bm = mock_beatmap_manager({
            "message": "Snapshotted 1 beatmap(s)",
            "updated_beatmapset": None,
            "updated_beatmaps": [],
            "snapshotted_beatmapset": {"id": 1, "beatmapset_id": self.TEST_BEATMAPSET_ID, "snapshot_number": 1, "checksum": "abc"},
            "snapshotted_beatmaps": [{"id": 1, "beatmap_id": 116383, "snapshot_number": 1, "checksum": "abc"}],
        })

        headers = {"Authorization": f"Bearer {admin_user_token}"}
        with patch('api.v1.beatmapsets.BeatmapManager', return_value=mock_bm), \
             patch('app.beatmaps.BeatmapManager', return_value=mock_bm), \
             patch('app.osu_api.OsuAPIClient', return_value=mock_osu_client):
            body = {"id": self.TEST_BEATMAPSET_ID}
            response = TestClient.post("/api/v1/beatmapsets", json=body, headers=headers)

        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert "Snapshotted" in data["message"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_bypass_security_with_flag(self, TestClient, mock_beatmap_manager, mock_osu_client):
        """Test DISABLE_SECURITY=True bypasses authorization."""
        os.environ["DISABLE_SECURITY"] = "True"

        mock_bm = mock_beatmap_manager({
            "message": "Snapshotted 1 beatmap(s)",
            "updated_beatmapset": None,
            "updated_beatmaps": [],
            "snapshotted_beatmapset": {"id": 1, "beatmapset_id": self.TEST_BEATMAPSET_ID, "snapshot_number": 1, "checksum": "abc"},
            "snapshotted_beatmaps": [{"id": 1, "beatmap_id": 116383, "snapshot_number": 1, "checksum": "abc"}],
        })

        with patch('api.v1.beatmapsets.BeatmapManager', return_value=mock_bm), \
             patch('app.beatmaps.BeatmapManager', return_value=mock_bm), \
             patch('app.osu_api.OsuAPIClient', return_value=mock_osu_client):
            body = {"id": self.TEST_BEATMAPSET_ID}
            response = TestClient.post("/api/v1/beatmapsets", json=body)

        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert "Snapshotted" in data["message"]

        del os.environ["DISABLE_SECURITY"]
