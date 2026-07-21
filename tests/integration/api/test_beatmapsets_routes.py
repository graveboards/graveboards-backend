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
    async def test_admin_archival_creates_snapshot(self, TestClientWithMocks, mock_beatmap_manager, mock_osu_client, security_disabled):
        """Test successful beatmap archival that creates new snapshot."""
        mock_bm = mock_beatmap_manager({
            "message": "Snapshotted 1 beatmap(s)",
            "updated_beatmapset": None,
            "updated_beatmaps": [],
            "snapshotted_beatmapset": {"id": 1, "beatmapset_id": self.TEST_BEATMAPSET_ID, "snapshot_number": 1, "checksum": "abc"},
            "snapshotted_beatmaps": [{"id": 1, "beatmap_id": 116383, "snapshot_number": 1, "checksum": "abc"}],
        })

        test_client = TestClientWithMocks()

        with patch('api.v1.beatmapsets.BeatmapManager', return_value=mock_bm), \
             patch('app.beatmaps.BeatmapManager', return_value=mock_bm), \
             patch('app.osu_api.OsuAPIClient', return_value=mock_osu_client):
            body = {"id": self.TEST_BEATMAPSET_ID}
            response = test_client.post("/api/v1/beatmapsets", json=body)

        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert "Snapshotted" in data["message"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_archival_updates_existing(self, TestClientWithMocks, mock_beatmap_manager, mock_osu_client, security_disabled):
        """Test successful beatmap archival that updates existing data."""
        mock_bm = mock_beatmap_manager({
            "message": "Updated 2 field(s) in the beatmapset and 1 field(s) in 1 beatmap(s)",
            "updated_beatmapset": {"beatmapset_id": self.TEST_BEATMAPSET_ID, "bpm": 130.0, "title": "New Title"},
            "updated_beatmaps": [{"beatmap_id": 116383, "version": "Hard"}],
            "snapshotted_beatmapset": None,
            "snapshotted_beatmaps": [],
        })

        test_client = TestClientWithMocks()

        with patch('api.v1.beatmapsets.BeatmapManager', return_value=mock_bm), \
             patch('app.beatmaps.BeatmapManager', return_value=mock_bm), \
             patch('app.osu_api.OsuAPIClient', return_value=mock_osu_client):
            body = {"id": self.TEST_BEATMAPSET_ID}
            response = test_client.post("/api/v1/beatmapsets", json=body)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Updated" in data["message"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_archival_up_to_date(self, TestClientWithMocks, mock_beatmap_manager, mock_osu_client, security_disabled):
        """Test successful beatmap archival that detects up-to-date data."""
        mock_bm = mock_beatmap_manager({
            "message": "The beatmapset and its beatmaps are fully up-to-date",
            "updated_beatmapset": None,
            "updated_beatmaps": [],
            "snapshotted_beatmapset": None,
            "snapshotted_beatmaps": [],
        })

        test_client = TestClientWithMocks()

        with patch('api.v1.beatmapsets.BeatmapManager', return_value=mock_bm), \
             patch('app.beatmaps.BeatmapManager', return_value=mock_bm), \
             patch('app.osu_api.OsuAPIClient', return_value=mock_osu_client):
            body = {"id": self.TEST_BEATMAPSET_ID}
            response = test_client.post("/api/v1/beatmapsets", json=body)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "fully up-to-date" in data["message"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_osu_api_error_handling(self, TestClientWithMocks, mock_beatmap_manager, mock_osu_client, security_disabled):
        """Test that osu! API errors are properly handled."""
        import httpx
        from httpx import Request

        mock_bm = mock_beatmap_manager(None)
        mock_response = httpx.Response(
            status_code=404,
            content=b'{"error": "Beatmapset not found"}',
            headers={"content-type": "application/json"},
        )
        mock_request = Request("GET", "https://osu.ppy.sh/api/v2/beatmapsets/999999")
        mock_bm.archive = AsyncMock(side_effect=httpx.HTTPStatusError(
            "Not Found",
            request=mock_request,
            response=mock_response,
        ))

        test_client = TestClientWithMocks()

        with patch('api.v1.beatmapsets.BeatmapManager', return_value=mock_bm), \
             patch('app.beatmaps.BeatmapManager', return_value=mock_bm), \
             patch('app.osu_api.OsuAPIClient', return_value=mock_osu_client), \
             patch('api.v1.beatmapsets.problem', return_value={"error": "Beatmapset not found"}):
            body = {"id": self.TEST_BEATMAPSET_ID}
            response = test_client.post("/api/v1/beatmapsets", json=body)

        assert response.status_code == 404
        data = response.json()
        assert "error" in str(data).lower() or "not found" in str(data.get("detail", "")).lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_non_admin_user_gets_forbidden(self, TestClientWithMocks, mock_beatmap_manager, mock_osu_client, authenticated_user_id):
        """Test that non-admin user gets 403 Forbidden."""
        from app.security import generate_token

        mock_bm = mock_beatmap_manager({
            "message": "Snapshotted 1 beatmap(s)",
            "updated_beatmapset": None,
            "updated_beatmaps": [],
            "snapshotted_beatmapset": {"id": 1, "beatmapset_id": self.TEST_BEATMAPSET_ID, "snapshot_number": 1, "checksum": "abc"},
            "snapshotted_beatmaps": [{"id": 1, "beatmap_id": 116383, "snapshot_number": 1, "checksum": "abc"}],
        })

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = 99999999
        mock_user.roles = []
        mock_db.get = AsyncMock(return_value=mock_user)
        mock_db.add = AsyncMock()
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('api.v1.beatmapsets.BeatmapManager', return_value=mock_bm), \
             patch('app.beatmaps.BeatmapManager', return_value=mock_bm), \
             patch('app.osu_api.OsuAPIClient', return_value=mock_osu_client), \
             authenticated_user_id(99999999):
            headers = {"Authorization": f"Bearer {generate_token(99999999)}"}
            body = {"id": self.TEST_BEATMAPSET_ID}
            response = test_client.post("/api/v1/beatmapsets", json=body, headers=headers)

        assert response.status_code == 403
        data = response.json()
        assert "forbidden" in data.get("detail", "").lower() or "not authorized" in data.get("detail", "").lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_access_succeeds_with_token(self, TestClientWithMocks, mock_beatmap_manager, mock_osu_client, admin_user_token, authenticated_user_id):
        """Test that admin user can successfully post beatmapset with valid token."""
        from app.security import decode_token
        from app.database.enums import RoleName

        mock_bm = mock_beatmap_manager({
            "message": "Snapshotted 1 beatmap(s)",
            "updated_beatmapset": None,
            "updated_beatmaps": [],
            "snapshotted_beatmapset": {"id": 1, "beatmapset_id": self.TEST_BEATMAPSET_ID, "snapshot_number": 1, "checksum": "abc"},
            "snapshotted_beatmaps": [{"id": 1, "beatmap_id": 116383, "snapshot_number": 1, "checksum": "abc"}],
        })

        decoded_token = decode_token(admin_user_token)
        user_id = int(decoded_token["sub"])

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = user_id
        admin_role = MagicMock()
        admin_role.name = RoleName.ADMIN.value
        mock_user.roles = [admin_role]
        mock_db.get = AsyncMock(return_value=mock_user)
        mock_db.add = AsyncMock()
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('api.v1.beatmapsets.BeatmapManager', return_value=mock_bm), \
             patch('app.beatmaps.BeatmapManager', return_value=mock_bm), \
             patch('app.osu_api.OsuAPIClient', return_value=mock_osu_client):
            with authenticated_user_id(user_id):
                headers = {"Authorization": f"Bearer {admin_user_token}"}
                body = {"id": self.TEST_BEATMAPSET_ID}
                response = test_client.post("/api/v1/beatmapsets", json=body, headers=headers)

        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert "Snapshotted" in data["message"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_success_with_auth(self, TestClientWithMocks, mock_beatmap_manager, mock_osu_client, admin_user_token):
        """Test that admin user can successfully post beatmapset with valid token."""
        from app.database.enums import RoleName

        mock_bm = mock_beatmap_manager({
            "message": "Snapshotted 1 beatmap(s)",
            "updated_beatmapset": None,
            "updated_beatmaps": [],
            "snapshotted_beatmapset": {"id": 1, "beatmapset_id": self.TEST_BEATMAPSET_ID, "snapshot_number": 1, "checksum": "abc"},
            "snapshotted_beatmaps": [{"id": 1, "beatmap_id": 116383, "snapshot_number": 1, "checksum": "abc"}],
        })

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = 11111111
        admin_role = MagicMock()
        admin_role.name = RoleName.ADMIN.value
        mock_user.roles = [admin_role]
        mock_db.get = AsyncMock(return_value=mock_user)

        headers = {"Authorization": f"Bearer {admin_user_token}"}
        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('api.v1.beatmapsets.BeatmapManager', return_value=mock_bm), \
             patch('app.beatmaps.BeatmapManager', return_value=mock_bm), \
             patch('app.osu_api.OsuAPIClient', return_value=mock_osu_client):
            body = {"id": self.TEST_BEATMAPSET_ID}
            response = test_client.post("/api/v1/beatmapsets", json=body, headers=headers)

        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert "Snapshotted" in data["message"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_bypass_security_with_flag(self, TestClientWithMocks, mock_beatmap_manager, mock_osu_client, security_disabled):
        """Test security disabled bypasses authorization."""
        mock_bm = mock_beatmap_manager({
            "message": "Snapshotted 1 beatmap(s)",
            "updated_beatmapset": None,
            "updated_beatmaps": [],
            "snapshotted_beatmapset": {"id": 1, "beatmapset_id": self.TEST_BEATMAPSET_ID, "snapshot_number": 1, "checksum": "abc"},
            "snapshotted_beatmaps": [{"id": 1, "beatmap_id": 116383, "snapshot_number": 1, "checksum": "abc"}],
        })

        test_client = TestClientWithMocks()

        with patch('api.v1.beatmapsets.BeatmapManager', return_value=mock_bm), \
             patch('app.beatmaps.BeatmapManager', return_value=mock_bm), \
             patch('app.osu_api.OsuAPIClient', return_value=mock_osu_client):
            body = {"id": self.TEST_BEATMAPSET_ID}
            response = test_client.post("/api/v1/beatmapsets", json=body)

        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert "Snapshotted" in data["message"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_beatmapset_list(self, TestClientWithMocks):
        """Test GET /api/v1/beatmapsets returns list of beatmapsets."""
        mock_db = AsyncMock()
        mock_beatmapset1 = MagicMock()
        mock_beatmapset1.id = 35965
        mock_beatmapset2 = MagicMock()
        mock_beatmapset2.id = 35966
        mock_db.get_many = AsyncMock(return_value=[mock_beatmapset1, mock_beatmapset2])

        test_client = TestClientWithMocks(mock_db=mock_db)

        response = test_client.get("/api/v1/beatmapsets")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_beatmapset_by_id(self, TestClientWithMocks):
        """Test GET /api/v1/beatmapsets/{id} returns specific beatmapset."""
        mock_db = AsyncMock()
        mock_beatmapset = MagicMock()
        mock_beatmapset.id = 35965
        mock_beatmapset.user_id = 12345678
        mock_db.get = AsyncMock(return_value=mock_beatmapset)

        test_client = TestClientWithMocks(mock_db=mock_db)

        response = test_client.get("/api/v1/beatmapsets/35965")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 35965

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_beatmapset_not_found(self, TestClientWithMocks):
        """Test GET /api/v1/beatmapsets/{id} returns 404 for non-existent beatmapset."""
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=None)

        test_client = TestClientWithMocks(mock_db=mock_db)

        response = test_client.get("/api/v1/beatmapsets/999999")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_beatmapset_zip(TestClientWithMocks):
    """Test GET /api/v1/beatmapsets/{id}/snapshots/{n}/zip returns zip file."""
    from app.beatmaps import BeatmapManager
    from io import BytesIO

    mock_db = AsyncMock()
    mock_beatmapset_snapshot = MagicMock()
    mock_beatmapset_snapshot.id = 1
    mock_beatmapset_snapshot.beatmapset_id = 35965
    mock_beatmapset_snapshot.snapshot_number = 1

    mock_beatmap_snapshot1 = MagicMock()
    mock_beatmap_snapshot1.beatmap_id = 116383
    mock_beatmap_snapshot1.snapshot_number = 1

    mock_beatmap_snapshot2 = MagicMock()
    mock_beatmap_snapshot2.beatmap_id = 116384
    mock_beatmap_snapshot2.snapshot_number = 1

    mock_beatmapset_snapshot.beatmap_snapshots = [mock_beatmap_snapshot1, mock_beatmap_snapshot2]
    mock_db.get = AsyncMock(return_value=mock_beatmapset_snapshot)

    mock_rc = AsyncMock()
    mock_bm = MagicMock()
    mock_bm.get_zip = AsyncMock(return_value=BytesIO(b"fake zip content"))

    test_client = TestClientWithMocks(mock_db=mock_db, mock_rc=mock_rc)

    with patch('api.v1.beatmapsets.snapshots.zip.BeatmapManager', return_value=mock_bm):
        response = test_client.get("/api/v1/beatmapsets/35965/snapshots/1/zip")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert "attachment" in response.headers["content-disposition"]
    assert "35965.zip" in response.headers["content-disposition"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_beatmapset_zip_not_found(TestClientWithMocks):
    """Test 404 when zip file doesn't exist."""
    mock_db = AsyncMock()
    mock_db.get = AsyncMock(return_value=None)

    mock_rc = AsyncMock()
    mock_bm = MagicMock()
    mock_bm.get_zip = AsyncMock(side_effect=ValueError("No snapshot found"))

    test_client = TestClientWithMocks(mock_db=mock_db, mock_rc=mock_rc)

    with patch('app.beatmaps.BeatmapManager', return_value=mock_bm):
        response = test_client.get("/api/v1/beatmapsets/999999/snapshots/1/zip")

    assert response.status_code == 404
    data = response.json()
    assert "snapshot" in data["detail"].lower() or "not found" in data["detail"].lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_snapshot(TestClientWithMocks):
    """Test GET /api/v1/beatmapsets/{id}/snapshots/{n} returns snapshot."""
    mock_db = AsyncMock()
    mock_beatmapset_snapshot = MagicMock()
    mock_beatmapset_snapshot.id = 1
    mock_beatmapset_snapshot.beatmapset_id = 35965
    mock_beatmapset_snapshot.snapshot_number = 1
    mock_beatmapset_snapshot.checksum = "abc123"
    mock_beatmapset_snapshot.created_at = "2024-01-01T00:00:00Z"
    mock_db.get = AsyncMock(return_value=mock_beatmapset_snapshot)

    test_client = TestClientWithMocks(mock_db=mock_db)

    with patch('app.database.schemas.beatmapset_snapshot.BeatmapsetSnapshotSchema.model_validate') as mock_validate:
        mock_validate.return_value = MagicMock(
            model_dump=MagicMock(return_value={
                "id": 1,
                "beatmapset_id": 35965,
                "snapshot_number": 1,
                "checksum": "abc123"
            })
        )
        response = test_client.get("/api/v1/beatmapsets/35965/snapshots/1")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["beatmapset_id"] == 35965
    assert data["snapshot_number"] == 1
    assert data["checksum"] == "abc123"
