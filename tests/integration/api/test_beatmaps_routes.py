import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.database.models import Beatmap, Beatmapset


@pytest.mark.integration
@pytest.mark.asyncio
async def test_beatmap_model_creation():
    beatmap = Beatmap(
        id=116383,
        beatmapset_id=35965
    )

    assert beatmap.id == 116383
    assert beatmap.beatmapset_id == 35965


@pytest.mark.integration
@pytest.mark.asyncio
async def test_beatmap_relationships():
    beatmap = Beatmap(
        id=116383,
        beatmapset_id=35965
    )

    assert hasattr(beatmap, 'beatmapset')
    assert hasattr(beatmap, 'snapshots')


@pytest.mark.integration
@pytest.mark.asyncio
async def test_beatmap_num_snapshots():
    beatmap = Beatmap(
        id=116383,
        beatmapset_id=35965
    )

    assert hasattr(beatmap, 'num_snapshots')


@pytest.mark.integration
@pytest.mark.asyncio
async def test_beatmapset_model_creation():
    beatmapset = Beatmapset(
        id=35965,
        user_id=12345678
    )

    assert beatmapset.id == 35965
    assert beatmapset.user_id == 12345678


@pytest.mark.integration
@pytest.mark.asyncio
async def test_beatmapset_relationships():
    beatmapset = Beatmapset(
        id=35965,
        user_id=12345678
    )

    assert hasattr(beatmapset, 'beatmaps')
    assert hasattr(beatmapset, 'snapshots')


@pytest.mark.integration
@pytest.mark.asyncio
async def test_beatmapset_num_snapshots():
    beatmapset = Beatmapset(
        id=35965,
        user_id=12345678
    )

    assert hasattr(beatmapset, 'num_snapshots')


@pytest.mark.integration
@pytest.mark.asyncio
async def test_beatmap_beatmapset_relationship():
    beatmapset = Beatmapset(
        id=35965,
        user_id=12345678
    )

    beatmap = Beatmap(
        id=116383,
        beatmapset_id=beatmapset.id
    )

    assert beatmap.beatmapset_id == beatmapset.id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_beatmapset_beatmap_relationship():
    beatmapset = Beatmapset(
        id=35965,
        user_id=12345678
    )

    beatmap1 = Beatmap(
        id=116383,
        beatmapset_id=beatmapset.id
    )

    beatmap2 = Beatmap(
        id=116384,
        beatmapset_id=beatmapset.id
    )

    assert beatmap1.beatmapset_id == beatmap2.beatmapset_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_beatmap_list(TestClientWithMocks):
    """Test GET /api/v1/beatmaps returns list of beatmaps."""
    mock_db = AsyncMock()
    mock_beatmap1 = MagicMock()
    mock_beatmap1.id = 116383
    mock_beatmap2 = MagicMock()
    mock_beatmap2.id = 116384
    mock_db.get_many = AsyncMock(return_value=[mock_beatmap1, mock_beatmap2])

    test_client = TestClientWithMocks(mock_db=mock_db)

    response = test_client.get("/api/v1/beatmaps")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_beatmap_by_id(TestClientWithMocks):
    """Test GET /api/v1/beatmaps/{id} returns specific beatmap."""
    mock_db = AsyncMock()
    mock_beatmap = MagicMock()
    mock_beatmap.id = 116383
    mock_beatmap.beatmapset_id = 35965
    mock_db.get = AsyncMock(return_value=mock_beatmap)

    test_client = TestClientWithMocks(mock_db=mock_db)

    response = test_client.get("/api/v1/beatmaps/116383")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 116383


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_beatmap_not_found(TestClientWithMocks):
    """Test GET /api/v1/beatmaps/{id} returns 404 for non-existent beatmap."""
    mock_db = AsyncMock()
    mock_db.get = AsyncMock(return_value=None)

    test_client = TestClientWithMocks(mock_db=mock_db)

    response = test_client.get("/api/v1/beatmaps/999999")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


class TestLeaderboardPatchIntegration:
    """Integration tests for PATCH /api/v1/beatmaps/{beatmap_id}/snapshots/{n}/leaderboard endpoint."""

    TEST_BEATMAP_ID = 116383
    TEST_SNAPSHOT_NUMBER = 1

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_can_update_leaderboard(self, TestClientWithMocks, admin_user_token):
        """Test admin can update leaderboard (e.g., freeze/unfreeze)."""
        from app.database.models import BeatmapSnapshot, Leaderboard

        mock_db = AsyncMock()
        
        beatmap_snapshot_data = {
            "id": 1,
            "beatmap_id": self.TEST_BEATMAP_ID,
            "snapshot_number": self.TEST_SNAPSHOT_NUMBER,
        }
        
        mock_beatmap_snapshot = MagicMock()
        mock_beatmap_snapshot.id = 1
        mock_beatmap_snapshot.beatmap_id = self.TEST_BEATMAP_ID
        mock_beatmap_snapshot.snapshot_number = self.TEST_SNAPSHOT_NUMBER
        
        leaderboard_data = {
            "id": 1,
            "beatmap_id": self.TEST_BEATMAP_ID,
            "beatmap_snapshot_id": 1,
            "frozen": False,
        }
        
        mock_leaderboard = MagicMock()
        mock_leaderboard.id = 1
        mock_leaderboard.beatmap_id = self.TEST_BEATMAP_ID
        mock_leaderboard.beatmap_snapshot_id = 1
        mock_leaderboard.frozen = False
        
        mock_user = MagicMock()
        mock_user.id = 11111111
        admin_role = MagicMock()
        admin_role.name = "admin"
        mock_user.roles = [admin_role]
        
        async def mock_get(model, **kwargs):
            if model == BeatmapSnapshot:
                return mock_beatmap_snapshot
            elif model == Leaderboard:
                return mock_leaderboard
            return mock_user
        
        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('app.security.decorators.DISABLE_SECURITY', False), \
             patch('app.security.decorators._get_authenticated_user_id', return_value=11111111):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.patch(
                f"/api/v1/beatmaps/{self.TEST_BEATMAP_ID}/snapshots/{self.TEST_SNAPSHOT_NUMBER}/leaderboard",
                json={"frozen": True},
                headers=headers
            )

        assert response.status_code == 200
        data = response.json()
        assert "updated successfully" in data["message"].lower()
        mock_db.update.assert_called_once()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_non_admin_gets_forbidden_on_leaderboard_patch(self, TestClientWithMocks, admin_user_token):
        """Test non-admin user gets 403 Forbidden on leaderboard patch."""
        from app.database.models import BeatmapSnapshot, Leaderboard

        mock_db = AsyncMock()
        
        beatmap_snapshot_data = {
            "id": 1,
            "beatmap_id": self.TEST_BEATMAP_ID,
            "snapshot_number": self.TEST_SNAPSHOT_NUMBER,
        }
        
        mock_beatmap_snapshot = MagicMock()
        mock_beatmap_snapshot.id = 1
        mock_beatmap_snapshot.beatmap_id = self.TEST_BEATMAP_ID
        mock_beatmap_snapshot.snapshot_number = self.TEST_SNAPSHOT_NUMBER
        
        mock_leaderboard = MagicMock()
        mock_leaderboard.id = 1
        mock_leaderboard.beatmap_id = self.TEST_BEATMAP_ID
        mock_leaderboard.beatmap_snapshot_id = 1
        
        mock_user = MagicMock()
        mock_user.id = 99999999
        mock_user.roles = []
        
        async def mock_get(model, **kwargs):
            return mock_user
        
        mock_db.get = AsyncMock(side_effect=mock_get)

        test_client = TestClientWithMocks(mock_db=mock_db)

        with patch('app.security.decorators.DISABLE_SECURITY', False), \
             patch('app.security.decorators._get_authenticated_user_id', return_value=99999999):
            headers = {"Authorization": "Bearer test_token_not_admin"}
            response = test_client.patch(
                f"/api/v1/beatmaps/{self.TEST_BEATMAP_ID}/snapshots/{self.TEST_SNAPSHOT_NUMBER}/leaderboard",
                json={"frozen": True},
                headers=headers
            )

        assert response.status_code == 403
        data = response.json()
        assert "forbidden" in data.get("detail", "").lower() or "not authorized" in data.get("detail", "").lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_beatmap_osu_file(TestClientWithMocks):
    """Test GET /api/v1/beatmaps/{id}/snapshots/{n}/osu returns .osu file."""
    mock_db = AsyncMock()
    mock_beatmap_snapshot = MagicMock()
    mock_beatmap_snapshot.id = 1
    mock_beatmap_snapshot.beatmap_id = 116383
    mock_beatmap_snapshot.snapshot_number = 1
    mock_db.get = AsyncMock(return_value=mock_beatmap_snapshot)

    mock_rc = AsyncMock()

    mock_bm = MagicMock()
    mock_bm.get_path = MagicMock(return_value="/data/beatmaps/116383/1.osu")

    test_client = TestClientWithMocks(mock_db=mock_db, mock_rc=mock_rc)

    class AsyncFileMock:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def read(self):
            return b"osu file content"

    mock_file = AsyncFileMock()

    with patch('api.v1.beatmaps.snapshots.osu.BeatmapManager', return_value=mock_bm), \
         patch('api.v1.beatmaps.snapshots.osu.aiofiles.open', return_value=mock_file):
        response = test_client.get("/api/v1/beatmaps/116383/snapshots/1/osu")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert "osu file content" in response.text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_beatmap_osu_file_not_found(TestClientWithMocks):
    """Test 404 when .osu file doesn't exist."""
    mock_db = AsyncMock()
    mock_beatmap_snapshot = MagicMock()
    mock_beatmap_snapshot.id = 1
    mock_beatmap_snapshot.beatmap_id = 116383
    mock_beatmap_snapshot.snapshot_number = 1
    mock_db.get = AsyncMock(return_value=mock_beatmap_snapshot)

    mock_rc = AsyncMock()
    mock_bm = MagicMock()
    mock_bm.get_path = MagicMock(return_value="/data/beatmaps/116383/1.osu")

    test_client = TestClientWithMocks(mock_db=mock_db, mock_rc=mock_rc)

    mock_file = MagicMock()
    mock_file.__aenter__ = MagicMock(side_effect=FileNotFoundError("File not found"))
    mock_file.__aexit__ = MagicMock(return_value=None)

    with patch('api.v1.beatmaps.snapshots.osu.BeatmapManager', return_value=mock_bm), \
         patch('api.v1.beatmaps.snapshots.osu.aiofiles.open', return_value=mock_file):
        response = test_client.get("/api/v1/beatmaps/116383/snapshots/1/osu")

    assert response.status_code == 404
    data = response.json()
    assert "osu file" in data["detail"].lower() or "not found" in data["detail"].lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_leaderboard(TestClientWithMocks):
    """Test GET /api/v1/beatmaps/{id}/snapshots/{n}/leaderboard returns leaderboard."""
    mock_db = AsyncMock()
    mock_beatmap_snapshot = MagicMock()
    mock_beatmap_snapshot.id = 1
    mock_beatmap_snapshot.beatmap_id = 116383
    mock_beatmap_snapshot.snapshot_number = 1
    mock_db.get = AsyncMock(return_value=mock_beatmap_snapshot)

    mock_leaderboard = MagicMock()
    mock_leaderboard.id = 1
    mock_leaderboard.beatmap_id = 116383
    mock_leaderboard.beatmap_snapshot_id = 1
    mock_leaderboard.frozen = False

    mock_db.get = AsyncMock(return_value=mock_leaderboard)

    test_client = TestClientWithMocks(mock_db=mock_db)

    with patch('api.v1.beatmaps.snapshots.leaderboard.LeaderboardSchema.model_validate') as mock_validate:
        mock_validate.return_value = MagicMock(
            model_dump=MagicMock(return_value={
                "id": 1,
                "beatmap_id": 116383,
                "beatmap_snapshot_id": 1,
                "frozen": False
            })
        )
        response = test_client.get("/api/v1/beatmaps/116383/snapshots/1/leaderboard")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["beatmap_id"] == 116383
    assert "frozen" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_admin_create_leaderboard(TestClientWithMocks, admin_user_token):
    """Test POST /api/v1/beatmaps/{id}/snapshots/{n}/leaderboard creates leaderboard."""
    mock_db = AsyncMock()
    mock_beatmap_snapshot = MagicMock()
    mock_beatmap_snapshot.id = 1
    mock_beatmap_snapshot.beatmap_id = 116383
    mock_beatmap_snapshot.snapshot_number = 1
    mock_db.get = AsyncMock(return_value=mock_beatmap_snapshot)

    mock_leaderboard = MagicMock()
    mock_leaderboard.id = 1
    mock_leaderboard.beatmap_id = 116383
    mock_leaderboard.beatmap_snapshot_id = 1
    mock_leaderboard.frozen = False

    mock_db.get = AsyncMock(side_effect=[mock_beatmap_snapshot, None])
    mock_db.add = AsyncMock()

    test_client = TestClientWithMocks(mock_db=mock_db)

    headers = {"Authorization": f"Bearer {admin_user_token}"}
    response = test_client.post(
        "/api/v1/beatmaps/116383/snapshots/1/leaderboard",
        json={"frozen": False},
        headers=headers
    )

    assert response.status_code == 201
    data = response.json()
    assert "added successfully" in data["message"].lower()
    mock_db.add.assert_called_once()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_admin_patch_leaderboard(TestClientWithMocks, admin_user_token):
    """Test PATCH /api/v1/beatmaps/{id}/snapshots/{n}/leaderboard updates leaderboard."""
    mock_db = AsyncMock()
    mock_beatmap_snapshot = MagicMock()
    mock_beatmap_snapshot.id = 1
    mock_beatmap_snapshot.beatmap_id = 116383
    mock_beatmap_snapshot.snapshot_number = 1
    mock_db.get = AsyncMock(return_value=mock_beatmap_snapshot)

    mock_leaderboard = MagicMock()
    mock_leaderboard.id = 1
    mock_leaderboard.beatmap_id = 116383
    mock_leaderboard.beatmap_snapshot_id = 1
    mock_leaderboard.frozen = False

    mock_db.get = AsyncMock(side_effect=[mock_beatmap_snapshot, mock_leaderboard])
    mock_db.update = AsyncMock()

    test_client = TestClientWithMocks(mock_db=mock_db)

    headers = {"Authorization": f"Bearer {admin_user_token}"}
    response = test_client.patch(
        "/api/v1/beatmaps/116383/snapshots/1/leaderboard",
        json={"frozen": True},
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "updated successfully" in data["message"].lower()
    mock_db.update.assert_called_once()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_leaderboard_scores(TestClientWithMocks):
    """Test GET /api/v1/beatmaps/{id}/snapshots/{n}/scores returns scores."""
    mock_db = AsyncMock()
    mock_beatmap_snapshot = MagicMock()
    mock_beatmap_snapshot.id = 1
    mock_beatmap_snapshot.beatmap_id = 116383
    mock_beatmap_snapshot.snapshot_number = 1
    mock_db.get = AsyncMock(return_value=mock_beatmap_snapshot)

    mock_leaderboard = MagicMock()
    mock_leaderboard.id = 1
    mock_leaderboard.beatmap_id = 116383
    mock_leaderboard.beatmap_snapshot_id = 1

    mock_score1 = MagicMock()
    mock_score1.id = 1001
    mock_score1.user_id = 123456
    mock_score1.rank = "S"
    mock_score1.score = 987654

    mock_score2 = MagicMock()
    mock_score2.id = 1002
    mock_score2.user_id = 789012
    mock_score2.rank = "A"
    mock_score2.score = 954321

    mock_leaderboard.scores = [mock_score1, mock_score2]
    mock_db.get = AsyncMock(return_value=mock_leaderboard)

    test_client = TestClientWithMocks(mock_db=mock_db)

    def mock_validate(obj):
        m = MagicMock()
        m.model_dump = MagicMock(return_value={
            "id": obj.id,
            "user_id": obj.user_id,
            "rank": obj.rank,
            "score": obj.score
        })
        return m

    with patch('api.v1.beatmaps.snapshots.scores.ScoreSchema.model_validate', side_effect=mock_validate):
        response = test_client.get("/api/v1/beatmaps/116383/snapshots/1/scores")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["score"] == 987654
    assert data[1]["score"] == 954321
