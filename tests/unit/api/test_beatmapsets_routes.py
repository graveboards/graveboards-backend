"""
Unit tests for POST /api/v1/beatmapsets endpoint (admin-only).

Tests the beatmap archival logic with mocked dependencies (fast, isolated).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.database.enums import RoleName


class TestBeatmapsetsPostEndpoint:
    """Integration tests for POST /api/v1/beatmapsets admin endpoint."""

    TEST_BEATMAPSET_ID = 35965

    # ==================== UNIT TESTS (Mocked Dependencies) ====================

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_post_beatmapsets_admin_creates_snapshot(self, unit_test_context):
        """Test successful beatmap archival by admin user (unit test)."""
        from api.v1.beatmapsets import post
        
        result = await post(
            body={"id": self.TEST_BEATMAPSET_ID},
            rc=unit_test_context["rc"],
            db=unit_test_context["db"],
            bm=unit_test_context["bm"],
        )
        
        assert result[1] == 201
        assert result[0]["message"] == "Snapshotted 1 beatmap(s)"
        assert "snapshotted_beatmapset" in result[0]
        assert "snapshotted_beatmaps" in result[0]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_post_beatmapsets_admin_updates(self, unit_test_context_update):
        """Test successful beatmap update by admin user (unit test)."""
        from api.v1.beatmapsets import post
        
        result = await post(
            body={"id": self.TEST_BEATMAPSET_ID},
            rc=unit_test_context_update["rc"],
            db=unit_test_context_update["db"],
            bm=unit_test_context_update["bm"],
        )
        
        assert result[1] == 200
        assert result[0]["message"] == "Updated 2 field(s) in the beatmapset and 1 field(s) in 1 beatmap(s)"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_post_beatmapsets_admin_up_to_date(self, unit_test_context_up_to_date):
        """Test beatmapset that is fully up-to-date (unit test)."""
        from api.v1.beatmapsets import post
        
        result = await post(
            body={"id": self.TEST_BEATMAPSET_ID},
            rc=unit_test_context_up_to_date["rc"],
            db=unit_test_context_up_to_date["db"],
            bm=unit_test_context_up_to_date["bm"],
        )
        
        assert result[1] == 200
        assert result[0]["message"] == "The beatmapset and its beatmaps are fully up-to-date"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_post_beatmapsets_osu_api_error(self, unit_test_context_error):
        """Test that osu! API errors are properly handled (unit test)."""
        import httpx
        from api.v1.beatmapsets import post
        
        result = await post(
            body={"id": self.TEST_BEATMAPSET_ID},
            rc=unit_test_context_error["rc"],
            db=unit_test_context_error["db"],
            bm=unit_test_context_error["bm"],
        )
        
        assert result[1] == 404
        assert "error" in result[0]

    # ==================== INTEGRATION TESTS (Full HTTP Stack) ====================

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_post_beatmapsets_admin_disabled_security(self, TestClient, db_session, clean_redis):
        """Test beatmap archival works with DISABLE_SECURITY=True (integration test)."""
        from app.config import DISABLE_SECURITY
        assert DISABLE_SECURITY is True
        
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
        
        with patch('app.beatmaps.BeatmapManager', return_value=mock_bm), \
             patch('api.v1.beatmapsets.BeatmapManager', return_value=mock_bm), \
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
    async def test_post_beatmapsets_admin_with_update(self, TestClient, db_session, clean_redis):
        """Test beatmap archival that updates existing data (integration test)."""
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
        
        with patch('app.beatmaps.BeatmapManager', return_value=mock_bm), \
             patch('api.v1.beatmapsets.BeatmapManager', return_value=mock_bm), \
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
    async def test_post_beatmapsets_admin_up_to_date(self, TestClient, db_session, clean_redis):
        """Test beatmap archival that detects up-to-date data (integration test)."""
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
        
        with patch('app.beatmaps.BeatmapManager', return_value=mock_bm), \
             patch('api.v1.beatmapsets.BeatmapManager', return_value=mock_bm), \
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
    async def test_post_beatmapsets_osu_api_error(self, TestClient, db_session, clean_redis):
        """Test that osu! API errors are properly handled (integration test)."""
        import httpx
        from unittest.mock import MagicMock
        
        mock_rc = AsyncMock()
        mock_rc.hgetall = AsyncMock(return_value=None)
        mock_rc.getdel = AsyncMock(return_value=None)
        
        mock_bm = MagicMock()
        mock_bm.archive = AsyncMock(side_effect=httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=MagicMock(status_code=404, json=lambda: {"error": "Beatmapset not found"}),
        ))
        
        with patch('app.beatmaps.BeatmapManager', return_value=mock_bm), \
             patch('api.v1.beatmapsets.BeatmapManager', return_value=mock_bm), \
             patch('app.osu_api.OsuAPIClient') as mock_osu_client:
            mock_osu_client.return_value.rc = mock_rc
            body = {"id": self.TEST_BEATMAPSET_ID}
            response = TestClient.post("/api/v1/beatmapsets", json=body)
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data


# ==================== Unit Test Context Fixtures ====================

@pytest.fixture
def unit_test_context():
    """Fixture providing unit test context with DISABLE_SECURITY=True."""
    import os
    original = os.environ.get("DISABLE_SECURITY")
    os.environ["DISABLE_SECURITY"] = "true"
    
    from unittest.mock import AsyncMock, MagicMock
    
    rc = AsyncMock()
    db = AsyncMock()
    bm = MagicMock()
    bm.archive = AsyncMock(return_value={
        "message": "Snapshotted 1 beatmap(s)",
        "updated_beatmapset": None,
        "updated_beatmaps": [],
        "snapshotted_beatmapset": {"id": 1, "beatmapset_id": 35965, "snapshot_number": 1, "checksum": "abc"},
        "snapshotted_beatmaps": [{"id": 1, "beatmap_id": 116383, "snapshot_number": 1, "checksum": "abc"}],
    })
    
    yield {"rc": rc, "db": db, "bm": bm}
    
    if original:
        os.environ["DISABLE_SECURITY"] = original
    else:
        os.environ.pop("DISABLE_SECURITY", None)


@pytest.fixture
def unit_test_context_update():
    """Fixture providing unit test context for update scenario."""
    import os
    original = os.environ.get("DISABLE_SECURITY")
    os.environ["DISABLE_SECURITY"] = "true"
    
    from unittest.mock import AsyncMock, MagicMock
    
    rc = AsyncMock()
    db = AsyncMock()
    bm = MagicMock()
    bm.archive = AsyncMock(return_value={
        "message": "Updated 2 field(s) in the beatmapset and 1 field(s) in 1 beatmap(s)",
        "updated_beatmapset": {"beatmapset_id": 35965, "bpm": 130.0, "title": "New Title"},
        "updated_beatmaps": [{"beatmap_id": 116383, "version": "Hard"}],
        "snapshotted_beatmapset": None,
        "snapshotted_beatmaps": [],
    })
    
    yield {"rc": rc, "db": db, "bm": bm}
    
    if original:
        os.environ["DISABLE_SECURITY"] = original
    else:
        os.environ.pop("DISABLE_SECURITY", None)


@pytest.fixture
def unit_test_context_up_to_date():
    """Fixture providing unit test context for up-to-date scenario."""
    import os
    original = os.environ.get("DISABLE_SECURITY")
    os.environ["DISABLE_SECURITY"] = "true"
    
    from unittest.mock import AsyncMock, MagicMock
    
    rc = AsyncMock()
    db = AsyncMock()
    bm = MagicMock()
    bm.archive = AsyncMock(return_value={
        "message": "The beatmapset and its beatmaps are fully up-to-date",
        "updated_beatmapset": None,
        "updated_beatmaps": [],
        "snapshotted_beatmapset": None,
        "snapshotted_beatmaps": [],
    })
    
    yield {"rc": rc, "db": db, "bm": bm}
    
    if original:
        os.environ["DISABLE_SECURITY"] = original
    else:
        os.environ.pop("DISABLE_SECURITY", None)


@pytest.fixture
def unit_test_context_error():
    """Fixture providing unit test context for error scenario."""
    import os
    original = os.environ.get("DISABLE_SECURITY")
    os.environ["DISABLE_SECURITY"] = "true"
    
    import httpx
    from unittest.mock import AsyncMock, MagicMock
    
    rc = AsyncMock()
    db = AsyncMock()
    bm = MagicMock()
    bm.archive = AsyncMock(side_effect=httpx.HTTPStatusError(
        "Not Found",
        request=MagicMock(),
        response=MagicMock(status_code=404, json=lambda: {"error": "Beatmapset not found"}),
    ))
    
    yield {"rc": rc, "db": db, "bm": bm}
    
    if original:
        os.environ["DISABLE_SECURITY"] = original
    else:
        os.environ.pop("DISABLE_SECURITY", None)
