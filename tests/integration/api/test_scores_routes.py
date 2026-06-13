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

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_submission_creates_score(self, TestClient, valid_score_body):
        """Test successful score submission that creates new score."""
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
        
        mock_db.get.side_effect = [
            mock_user,
            mock_beatmap,
            mock_snapshot,
            mock_leaderboard,
            None,
        ]
        mock_db.add = AsyncMock()

        from app.test_app import MockDatabaseMiddleware

        original_call = MockDatabaseMiddleware.__call__

        async def patched_call(self, scope, receive, send):
            scope["state"]["db"] = mock_db
            await self.app(scope, receive, send)

        MockDatabaseMiddleware.__call__ = patched_call

        try:
            response = TestClient.post("/api/v1/scores", json=valid_score_body)
        finally:
            MockDatabaseMiddleware.__call__ = original_call

        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert data["message"] == "Score added successfully!"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_user_not_found(self, TestClient, valid_score_body):
        """Test score submission fails when user doesn't exist."""
        mock_db = AsyncMock()
        mock_db.get.return_value = None
        mock_db.add = AsyncMock()

        from app.test_app import MockDatabaseMiddleware

        original_call = MockDatabaseMiddleware.__call__

        async def patched_call(self, scope, receive, send):
            scope["state"]["db"] = mock_db
            await self.app(scope, receive, send)

        MockDatabaseMiddleware.__call__ = patched_call

        try:
            body = valid_score_body.copy()
            body["user_id"] = -1
            response = TestClient.post("/api/v1/scores", json=body)
        finally:
            MockDatabaseMiddleware.__call__ = original_call

        assert response.status_code == 404
        data = response.json()
        assert f"There is no user with ID" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_beatmap_not_found(self, TestClient, valid_score_body):
        """Test score submission fails when beatmap doesn't exist."""
        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = self.TEST_USER_ID
        mock_db.get.side_effect = [mock_user, None]
        mock_db.add = AsyncMock()

        from app.test_app import MockDatabaseMiddleware

        original_call = MockDatabaseMiddleware.__call__

        async def patched_call(self, scope, receive, send):
            scope["state"]["db"] = mock_db
            await self.app(scope, receive, send)

        MockDatabaseMiddleware.__call__ = patched_call

        try:
            body = valid_score_body.copy()
            body["beatmap"]["id"] = -1
            response = TestClient.post("/api/v1/scores", json=body)
        finally:
            MockDatabaseMiddleware.__call__ = original_call

        assert response.status_code == 404
        data = response.json()
        assert f"There is no beatmap with ID" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_beatmap_snapshot_not_found(self, TestClient, valid_score_body):
        """Test score submission fails when beatmap snapshot doesn't exist."""
        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = self.TEST_USER_ID
        mock_beatmap = MagicMock()
        mock_beatmap.id = self.TEST_BEATMAP_ID
        mock_db.get.side_effect = [mock_user, mock_beatmap, None]
        mock_db.add = AsyncMock()

        from app.test_app import MockDatabaseMiddleware

        original_call = MockDatabaseMiddleware.__call__

        async def patched_call(self, scope, receive, send):
            scope["state"]["db"] = mock_db
            await self.app(scope, receive, send)

        MockDatabaseMiddleware.__call__ = patched_call

        try:
            body = valid_score_body.copy()
            body["beatmap"]["id"] = -1
            response = TestClient.post("/api/v1/scores", json=body)
        finally:
            MockDatabaseMiddleware.__call__ = original_call

        assert response.status_code == 404
        data = response.json()
        assert f"There is no beatmap snapshot" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_leaderboard_not_found(self, TestClient, valid_score_body):
        """Test score submission fails when leaderboard doesn't exist."""
        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = self.TEST_USER_ID
        mock_beatmap = MagicMock()
        mock_beatmap.id = self.TEST_BEATMAP_ID
        mock_snapshot = MagicMock()
        mock_snapshot.id = 1
        mock_snapshot.beatmap_id = self.TEST_BEATMAP_ID
        mock_db.get.side_effect = [mock_user, mock_beatmap, mock_snapshot, None]
        mock_db.add = AsyncMock()

        from app.test_app import MockDatabaseMiddleware

        original_call = MockDatabaseMiddleware.__call__

        async def patched_call(self, scope, receive, send):
            scope["state"]["db"] = mock_db
            await self.app(scope, receive, send)

        MockDatabaseMiddleware.__call__ = patched_call

        try:
            body = valid_score_body.copy()
            body["beatmap"]["id"] = -1
            response = TestClient.post("/api/v1/scores", json=body)
        finally:
            MockDatabaseMiddleware.__call__ = original_call

        assert response.status_code == 404
        data = response.json()
        assert f"There is no leaderboard" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_duplicate_score(self, TestClient, valid_score_body):
        """Test score submission fails when duplicate exists."""
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
        mock_db.add = AsyncMock()

        from app.test_app import MockDatabaseMiddleware

        original_call = MockDatabaseMiddleware.__call__

        async def patched_call(self, scope, receive, send):
            scope["state"]["db"] = mock_db
            await self.app(scope, receive, send)

        MockDatabaseMiddleware.__call__ = patched_call

        try:
            body = valid_score_body.copy()
            body["beatmap"]["id"] = -1
            response = TestClient.post("/api/v1/scores", json=body)
        finally:
            MockDatabaseMiddleware.__call__ = original_call

        assert response.status_code == 409
        data = response.json()
        assert "already exists" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_non_admin_user_gets_forbidden(self, TestClient, valid_score_body):
        """Test that non-admin user gets 403 Forbidden."""
        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = 99999999
        mock_user.roles = []
        mock_db.get = AsyncMock(return_value=mock_user)
        mock_db.add = AsyncMock()

        from app.test_app import MockDatabaseMiddleware

        original_call = MockDatabaseMiddleware.__call__

        async def patched_call(self, scope, receive, send):
            scope["state"]["db"] = mock_db
            await self.app(scope, receive, send)

        MockDatabaseMiddleware.__call__ = patched_call

        try:
            with patch('app.security.decorators.DISABLE_SECURITY', False), \
                 patch('app.security.decorators._get_authenticated_user_id', return_value=99999999):
                headers = {"Authorization": "Bearer test_token_not_admin"}
                response = TestClient.post("/api/v1/scores", json=valid_score_body, headers=headers)
        finally:
            MockDatabaseMiddleware.__call__ = original_call

        assert response.status_code == 403
        data = response.json()
        assert "forbidden" in data.get("detail", "").lower() or "not authorized" in data.get("detail", "").lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_access_succeeds_with_token(self, TestClient, valid_score_body, admin_user_token):
        """Test that admin user can successfully post score with valid token."""
        from app.security import decode_token
        from app.database.enums import RoleName

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

        mock_db.get.side_effect = [
            mock_user,
            mock_beatmap,
            mock_snapshot,
            mock_leaderboard,
            None,
        ]
        mock_db.add = AsyncMock()

        from app.test_app import MockDatabaseMiddleware

        original_call = MockDatabaseMiddleware.__call__

        async def patched_call(self, scope, receive, send):
            scope["state"]["db"] = mock_db
            await self.app(scope, receive, send)

        MockDatabaseMiddleware.__call__ = patched_call

        try:
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = TestClient.post("/api/v1/scores", json=valid_score_body, headers=headers)
        finally:
            MockDatabaseMiddleware.__call__ = original_call

        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert data["message"] == "Score added successfully!"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_success_with_auth(self, TestClient, valid_score_body, admin_user_token):
        """Test that admin user can successfully post score with valid token."""
        from app.test_app import MockDatabaseMiddleware

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
        mock_db.get.side_effect = [
            mock_user,
            mock_beatmap,
            mock_snapshot,
            mock_leaderboard,
            None,
        ]
        mock_db.add = AsyncMock()

        original_call = MockDatabaseMiddleware.__call__

        async def patched_call(self, scope, receive, send):
            scope["state"]["db"] = mock_db
            await self.app(scope, receive, send)

        MockDatabaseMiddleware.__call__ = patched_call

        try:
            headers = {"Authorization": f"Bearer {admin_user_token}"}
            response = TestClient.post("/api/v1/scores", json=valid_score_body, headers=headers)
        finally:
            MockDatabaseMiddleware.__call__ = original_call

        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert data["message"] == "Score added successfully!"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_bypass_security_with_flag(self, TestClient, valid_score_body):
        """Test DISABLE_SECURITY=True bypasses authorization."""
        from app.test_app import MockDatabaseMiddleware

        os.environ["DISABLE_SECURITY"] = "True"

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
        mock_db.get.side_effect = [
            mock_user,
            mock_beatmap,
            mock_snapshot,
            mock_leaderboard,
            None,
        ]
        mock_db.add = AsyncMock()

        original_call = MockDatabaseMiddleware.__call__

        async def patched_call(self, scope, receive, send):
            scope["state"]["db"] = mock_db
            await self.app(scope, receive, send)

        MockDatabaseMiddleware.__call__ = patched_call

        try:
            response = TestClient.post("/api/v1/scores", json=valid_score_body)
        finally:
            MockDatabaseMiddleware.__call__ = original_call
            del os.environ["DISABLE_SECURITY"]

        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert data["message"] == "Score added successfully!"
