"""
Integration tests for POST /api/v1/scores endpoint (admin-only).

Tests the score submission via full HTTP stack.
"""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestScoresPostIntegration:
    """Integration tests for POST /api/v1/scores admin endpoint."""

    TEST_USER_ID = 12345678
    TEST_BEATMAP_ID = 116383
    TEST_SCORE_CREATED_AT = "2024-01-15T12:30:45+00:00"

    @pytest.fixture
    def valid_score_body(self):
        """Return a valid score submission body."""
        return {
            "user_id": self.TEST_USER_ID,
            "beatmap": {"id": self.TEST_BEATMAP_ID},
            "created_at": self.TEST_SCORE_CREATED_AT,
            "score": 100000,
            "max_combo": 500,
            "rank": "SSH",
            "statistics": {
                "count_300": 300,
                "count_100": 50,
                "count_50": 10,
                "count_miss": 0,
            },
        }

    @pytest.fixture
    def admin_role_user(self):
        """A User mock role_authorization's role check resolves the (disabled-security)
        dev identity to - admin-roled, so it's distinguishable from the handler's own
        `db.get(User, id=user_id)` lookup, which doesn't request `_include={"roles"}`.
        """
        from app.database.enums import RoleName

        admin_role = MagicMock()
        admin_role.name = RoleName.ADMIN.value
        mock_admin_user = MagicMock()
        mock_admin_user.roles = [admin_role]
        return mock_admin_user

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_submission_creates_score(self, TestClientWithMocks, valid_score_body, admin_role_user, security_disabled):
        """Test successful score submission that creates new score."""
        from app.database.models import User, Beatmap, BeatmapSnapshot, Leaderboard, Score

        mock_db = AsyncMock()

        mock_user = MagicMock()
        mock_user.id = self.TEST_USER_ID
        mock_beatmap = MagicMock()
        mock_beatmap.id = self.TEST_BEATMAP_ID
        mock_snapshot = MagicMock()
        mock_snapshot.id = 1
        mock_snapshot.beatmap_id = self.TEST_BEATMAP_ID
        mock_leaderboard = MagicMock()
        mock_leaderboard.id = 1

        async def mock_get(model, **kwargs):
            if model == User and kwargs.get("_include", {}).get("roles"):
                return admin_role_user
            if model == User:
                return mock_user
            if model == Beatmap:
                return mock_beatmap
            if model == BeatmapSnapshot:
                return mock_snapshot
            if model == Leaderboard:
                return mock_leaderboard
            if model == Score:
                return None
            return None

        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.add = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        response = test_client.post("/api/v1/scores", json=valid_score_body)

        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert data["message"] == "Score added successfully!"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_user_not_found(self, TestClientWithMocks, valid_score_body, admin_role_user, security_disabled):
        """Test score submission fails when user doesn't exist."""
        from app.database.models import User

        mock_db = AsyncMock()

        async def mock_get(model, **kwargs):
            if model == User and kwargs.get("_include", {}).get("roles"):
                return admin_role_user
            return None

        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.add = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        body = valid_score_body.copy()
        body["user_id"] = -1
        response = test_client.post("/api/v1/scores", json=body)

        assert response.status_code == 404
        data = response.json()
        assert f"There is no user with ID" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_beatmap_not_found(self, TestClientWithMocks, valid_score_body, admin_role_user, security_disabled):
        """Test score submission fails when beatmap doesn't exist."""
        from app.database.models import User, Beatmap

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = self.TEST_USER_ID

        async def mock_get(model, **kwargs):
            if model == User and kwargs.get("_include", {}).get("roles"):
                return admin_role_user
            if model == User:
                return mock_user
            if model == Beatmap:
                return None
            return None

        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.add = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        body = valid_score_body.copy()
        body["beatmap"]["id"] = -1
        response = test_client.post("/api/v1/scores", json=body)

        assert response.status_code == 404
        data = response.json()
        assert f"There is no beatmap with ID" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_beatmap_snapshot_not_found(self, TestClientWithMocks, valid_score_body, admin_role_user, security_disabled):
        """Test score submission fails when beatmap snapshot doesn't exist."""
        from app.database.models import User, Beatmap, BeatmapSnapshot

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = self.TEST_USER_ID
        mock_beatmap = MagicMock()
        mock_beatmap.id = self.TEST_BEATMAP_ID

        async def mock_get(model, **kwargs):
            if model == User and kwargs.get("_include", {}).get("roles"):
                return admin_role_user
            if model == User:
                return mock_user
            if model == Beatmap:
                return mock_beatmap
            if model == BeatmapSnapshot:
                return None
            return None

        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.add = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        body = valid_score_body.copy()
        body["beatmap"]["id"] = -1
        response = test_client.post("/api/v1/scores", json=body)

        assert response.status_code == 404
        data = response.json()
        assert f"There is no beatmap snapshot" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_leaderboard_not_found(self, TestClientWithMocks, valid_score_body, admin_role_user, security_disabled):
        """Test score submission fails when leaderboard doesn't exist."""
        from app.database.models import User, Beatmap, BeatmapSnapshot, Leaderboard

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = self.TEST_USER_ID
        mock_beatmap = MagicMock()
        mock_beatmap.id = self.TEST_BEATMAP_ID
        mock_snapshot = MagicMock()
        mock_snapshot.id = 1
        mock_snapshot.beatmap_id = self.TEST_BEATMAP_ID

        async def mock_get(model, **kwargs):
            if model == User and kwargs.get("_include", {}).get("roles"):
                return admin_role_user
            if model == User:
                return mock_user
            if model == Beatmap:
                return mock_beatmap
            if model == BeatmapSnapshot:
                return mock_snapshot
            if model == Leaderboard:
                return None
            return None

        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.add = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        body = valid_score_body.copy()
        body["beatmap"]["id"] = -1
        response = test_client.post("/api/v1/scores", json=body)

        assert response.status_code == 404
        data = response.json()
        assert f"There is no leaderboard" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_duplicate_score(self, TestClientWithMocks, valid_score_body, admin_role_user, security_disabled):
        """Test score submission fails when duplicate exists."""
        from app.database.models import User, Beatmap, BeatmapSnapshot, Leaderboard, Score

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = self.TEST_USER_ID
        mock_beatmap = MagicMock()
        mock_beatmap.id = self.TEST_BEATMAP_ID
        mock_snapshot = MagicMock()
        mock_snapshot.id = 1
        mock_snapshot.beatmap_id = self.TEST_BEATMAP_ID
        mock_leaderboard = MagicMock()
        mock_leaderboard.id = 1
        mock_existing_score = MagicMock()

        async def mock_get(model, **kwargs):
            if model == User and kwargs.get("_include", {}).get("roles"):
                return admin_role_user
            if model == User:
                return mock_user
            if model == Beatmap:
                return mock_beatmap
            if model == BeatmapSnapshot:
                return mock_snapshot
            if model == Leaderboard:
                return mock_leaderboard
            if model == Score:
                return mock_existing_score
            return None

        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.add = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        body = valid_score_body.copy()
        body["beatmap"]["id"] = -1
        response = test_client.post("/api/v1/scores", json=body)

        assert response.status_code == 409
        data = response.json()
        assert "already exists" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_non_admin_user_gets_forbidden(self, TestClientWithMocks, valid_score_body, authenticated_user_id):
        """Test that non-admin user gets 403 Forbidden."""
        from app.security import generate_token

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = 99999999
        mock_user.roles = []
        mock_db.get = AsyncMock(return_value=mock_user)
        mock_db.add = AsyncMock()
        mock_db.update = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with authenticated_user_id(99999999):
            headers = {"Authorization": f"Bearer {generate_token(99999999)}"}
            response = test_client.post("/api/v1/scores", json=valid_score_body, headers=headers)

        assert response.status_code == 403
        data = response.json()
        assert "forbidden" in data.get("detail", "").lower() or "not authorized" in data.get("detail", "").lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_access_succeeds_with_token(self, TestClientWithMocks, valid_score_body, admin_user_token, authenticated_user_id):
        """Test that admin user can successfully post score with valid token."""
        from app.security import decode_token
        from app.database.enums import RoleName
        from app.database.models import User, Beatmap, BeatmapSnapshot, Leaderboard, Score

        decoded_token = decode_token(admin_user_token)
        user_id = int(decoded_token["sub"])
        
        mock_db = AsyncMock()
        
        mock_user = MagicMock()
        mock_user.id = user_id
        admin_role = MagicMock()
        admin_role.name = RoleName.ADMIN.value
        mock_user.roles = [admin_role]

        mock_beatmap = MagicMock()
        mock_beatmap.id = self.TEST_BEATMAP_ID

        mock_snapshot = MagicMock()
        mock_snapshot.id = 1
        mock_snapshot.beatmap_id = self.TEST_BEATMAP_ID

        mock_leaderboard = MagicMock()
        mock_leaderboard.id = 1

        async def mock_get(model, **kwargs):
            if model == User:
                return mock_user
            elif model == Beatmap:
                return mock_beatmap
            elif model == BeatmapSnapshot:
                return mock_snapshot
            elif model == Leaderboard:
                return mock_leaderboard
            elif model == Score:
                return None
            return None

        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.add = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        with authenticated_user_id(user_id):
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = test_client.post("/api/v1/scores", json=valid_score_body, headers=headers)

        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert data["message"] == "Score added successfully!"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_success_with_auth(self, TestClientWithMocks, valid_score_body, admin_user_token):
        """Test that admin user can successfully post score with valid token."""
        from app.database.models import User, Beatmap, BeatmapSnapshot, Leaderboard, Score

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = self.TEST_USER_ID
        admin_role = MagicMock()
        admin_role.name = "admin"
        mock_user.roles = [admin_role]
        mock_beatmap = MagicMock()
        mock_beatmap.id = self.TEST_BEATMAP_ID
        mock_snapshot = MagicMock()
        mock_snapshot.id = 1
        mock_snapshot.beatmap_id = self.TEST_BEATMAP_ID
        mock_leaderboard = MagicMock()
        mock_leaderboard.id = 1

        async def mock_get(model, **kwargs):
            if model == User:
                return mock_user
            if model == Beatmap:
                return mock_beatmap
            if model == BeatmapSnapshot:
                return mock_snapshot
            if model == Leaderboard:
                return mock_leaderboard
            if model == Score:
                return None
            return None

        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.add = AsyncMock()

        headers = {"Authorization": f"Bearer {admin_user_token}"}
        test_client = TestClientWithMocks(mock_db=mock_db)

        response = test_client.post("/api/v1/scores", json=valid_score_body, headers=headers)

        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert data["message"] == "Score added successfully!"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_bypass_security_with_flag(self, TestClientWithMocks, valid_score_body, admin_role_user, security_disabled):
        """Test that disabling security resolves an admin dev identity (rather than
        skipping the check outright), letting the request through.
        """
        from app.database.models import User, Beatmap, BeatmapSnapshot, Leaderboard, Score

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = self.TEST_USER_ID
        mock_beatmap = MagicMock()
        mock_beatmap.id = self.TEST_BEATMAP_ID
        mock_snapshot = MagicMock()
        mock_snapshot.id = 1
        mock_snapshot.beatmap_id = self.TEST_BEATMAP_ID
        mock_leaderboard = MagicMock()
        mock_leaderboard.id = 1

        async def mock_get(model, **kwargs):
            if model == User and kwargs.get("_include", {}).get("roles"):
                return admin_role_user
            if model == User:
                return mock_user
            if model == Beatmap:
                return mock_beatmap
            if model == BeatmapSnapshot:
                return mock_snapshot
            if model == Leaderboard:
                return mock_leaderboard
            if model == Score:
                return None
            return None

        mock_db.get = AsyncMock(side_effect=mock_get)
        mock_db.add = AsyncMock()

        test_client = TestClientWithMocks(mock_db=mock_db)

        response = test_client.post("/api/v1/scores", json=valid_score_body)

        assert response.status_code == 201
        data = response.json()
        assert "message" in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_score_list(self, TestClientWithMocks):
        """Test GET /api/v1/scores returns list of scores."""
        from app.database.schemas import ScoreSchema, ScoreStatisticsSchema
        from pydantic import TypeAdapter
        from datetime import datetime

        mock_db = AsyncMock()
        
        score_data_1 = {
            "id": 1,
            "user_id": self.TEST_USER_ID,
            "beatmap": {"id": self.TEST_BEATMAP_ID},
            "beatmapset": {"id": 35965},
            "beatmap_id": self.TEST_BEATMAP_ID,
            "beatmapset_id": 35965,
            "leaderboard_id": 1,
            "accuracy": 99.99,
            "created_at": datetime.fromisoformat("2024-01-15T12:30:45+00:00"),
            "max_combo": 500,
            "mode": "osu",
            "mode_int": 0,
            "mods": [],
            "perfect": False,
            "pp": None,
            "rank": "SSH",
            "score": 100000,
            "statistics": {
                "count_300": 300,
                "count_100": 50,
                "count_50": 10,
                "count_miss": 0,
                "count_geki": 0,
                "count_katu": 0,
            },
            "type": "approved",
        }
        score_data_2 = {
            "id": 2,
            "user_id": self.TEST_USER_ID + 1,
            "beatmap": {"id": self.TEST_BEATMAP_ID},
            "beatmapset": {"id": 35965},
            "beatmap_id": self.TEST_BEATMAP_ID,
            "beatmapset_id": 35965,
            "leaderboard_id": 1,
            "accuracy": 98.5,
            "created_at": datetime.fromisoformat("2024-01-16T12:30:45+00:00"),
            "max_combo": 450,
            "mode": "osu",
            "mode_int": 0,
            "mods": [],
            "perfect": False,
            "pp": None,
            "rank": "S",
            "score": 95000,
            "statistics": {
                "count_300": 280,
                "count_100": 45,
                "count_50": 15,
                "count_miss": 5,
                "count_geki": 0,
                "count_katu": 0,
            },
            "type": "approved",
        }
        
        mock_score1 = ScoreSchema.model_validate(score_data_1)
        mock_score2 = ScoreSchema.model_validate(score_data_2)
        mock_db.get_many = AsyncMock(return_value=[mock_score1, mock_score2])

        test_client = TestClientWithMocks(mock_db=mock_db)

        response = test_client.get("/api/v1/scores")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_score_by_id(self, TestClientWithMocks):
        """Test GET /api/v1/scores/{id} returns specific score."""
        from app.database.schemas import ScoreSchema
        from datetime import datetime

        mock_db = AsyncMock()
        
        score_data = {
            "id": 1,
            "user_id": self.TEST_USER_ID,
            "beatmap": {"id": self.TEST_BEATMAP_ID},
            "beatmapset": {"id": 35965},
            "beatmap_id": self.TEST_BEATMAP_ID,
            "beatmapset_id": 35965,
            "leaderboard_id": 1,
            "accuracy": 99.99,
            "created_at": datetime.fromisoformat("2024-01-15T12:30:45+00:00"),
            "max_combo": 500,
            "mode": "osu",
            "mode_int": 0,
            "mods": [],
            "perfect": False,
            "pp": None,
            "rank": "SSH",
            "score": 100000,
            "statistics": {
                "count_300": 300,
                "count_100": 50,
                "count_50": 10,
                "count_miss": 0,
                "count_geki": 0,
                "count_katu": 0,
            },
            "type": "approved",
        }
        
        mock_score = ScoreSchema.model_validate(score_data)
        mock_db.get = AsyncMock(return_value=mock_score)

        test_client = TestClientWithMocks(mock_db=mock_db)

        response = test_client.get("/api/v1/scores/1")

        assert response.status_code == 200
        data = response.json()
        assert "id" in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_score_not_found(self, TestClientWithMocks):
        """Test GET /api/v1/scores/{id} returns 404 for non-existent score."""
        from app.database.models import Score

        mock_db = AsyncMock()
        
        async def mock_get(model, **kwargs):
            if model.__name__ == "Score":
                return None
            mock_user = MagicMock()
            mock_user.id = 12345678
            mock_user.roles = []
            return mock_user
        
        mock_db.get = AsyncMock(side_effect=mock_get)

        test_client = TestClientWithMocks(mock_db=mock_db)

        response = test_client.get("/api/v1/scores/999999")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
