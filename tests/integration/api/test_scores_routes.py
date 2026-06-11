"""
Integration tests for POST /api/v1/scores endpoint (admin-only).

Tests the score submission via full HTTP stack with mocked dependencies.
"""
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
    async def test_admin_disabled_security(self, TestClient, valid_score_body):
        """Test score submission works with DISABLE_SECURITY=True (integration)."""
        from app.test_app import MockDatabaseMiddleware
        
        mock_user = MagicMock()
        mock_user.id = self.TEST_USER_ID
        mock_beatmap = MagicMock()
        mock_beatmap.id = self.TEST_BEATMAP_ID
        mock_snapshot = MagicMock()
        mock_snapshot.id = 1
        mock_snapshot.beatmap_id = self.TEST_BEATMAP_ID
        mock_leaderboard = MagicMock()
        mock_leaderboard.id = 1
        
        mock_db = AsyncMock()
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
        
        assert response.status_code == 201
        data = response.json()
        assert "message" in data
        assert data["message"] == "Score added successfully!"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_user_not_found(self, TestClient, valid_score_body):
        """Test score submission fails when user doesn't exist (integration)."""
        from app.test_app import MockDatabaseMiddleware
        
        mock_db = AsyncMock()
        mock_db.get.side_effect = [None]
        
        original_call = MockDatabaseMiddleware.__call__
        
        async def patched_call(self, scope, receive, send):
            scope["state"]["db"] = mock_db
            await self.app(scope, receive, send)
        
        MockDatabaseMiddleware.__call__ = patched_call
        
        try:
            response = TestClient.post("/api/v1/scores", json=valid_score_body)
        finally:
            MockDatabaseMiddleware.__call__ = original_call
        
        assert response.status_code == 404
        data = response.json()
        assert f"There is no user with ID '{self.TEST_USER_ID}'" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_beatmap_not_found(self, TestClient, valid_score_body):
        """Test score submission fails when beatmap doesn't exist (integration)."""
        from app.test_app import MockDatabaseMiddleware
        
        mock_db = AsyncMock()
        mock_db.get.side_effect = [
            MagicMock(id=self.TEST_USER_ID),
            None,
        ]
        
        original_call = MockDatabaseMiddleware.__call__
        
        async def patched_call(self, scope, receive, send):
            scope["state"]["db"] = mock_db
            await self.app(scope, receive, send)
        
        MockDatabaseMiddleware.__call__ = patched_call
        
        try:
            response = TestClient.post("/api/v1/scores", json=valid_score_body)
        finally:
            MockDatabaseMiddleware.__call__ = original_call
        
        assert response.status_code == 404
        data = response.json()
        assert f"There is no beatmap with ID '{self.TEST_BEATMAP_ID}'" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_beatmap_snapshot_not_found(self, TestClient, valid_score_body):
        """Test score submission fails when beatmap snapshot doesn't exist (integration)."""
        from app.test_app import MockDatabaseMiddleware
        
        mock_db = AsyncMock()
        mock_db.get.side_effect = [
            MagicMock(id=self.TEST_USER_ID),
            MagicMock(id=self.TEST_BEATMAP_ID),
            None,
        ]
        
        original_call = MockDatabaseMiddleware.__call__
        
        async def patched_call(self, scope, receive, send):
            scope["state"]["db"] = mock_db
            await self.app(scope, receive, send)
        
        MockDatabaseMiddleware.__call__ = patched_call
        
        try:
            response = TestClient.post("/api/v1/scores", json=valid_score_body)
        finally:
            MockDatabaseMiddleware.__call__ = original_call
        
        assert response.status_code == 404
        data = response.json()
        assert f"There is no beatmap snapshot with beatmap ID '{self.TEST_BEATMAP_ID}'" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_leaderboard_not_found(self, TestClient, valid_score_body):
        """Test score submission fails when leaderboard doesn't exist (integration)."""
        from app.test_app import MockDatabaseMiddleware
        
        mock_db = AsyncMock()
        mock_db.get.side_effect = [
            MagicMock(id=self.TEST_USER_ID),
            MagicMock(id=self.TEST_BEATMAP_ID),
            MagicMock(id=1, beatmap_id=self.TEST_BEATMAP_ID, snapshot_number=1),
            None,
        ]
        
        original_call = MockDatabaseMiddleware.__call__
        
        async def patched_call(self, scope, receive, send):
            scope["state"]["db"] = mock_db
            await self.app(scope, receive, send)
        
        MockDatabaseMiddleware.__call__ = patched_call
        
        try:
            response = TestClient.post("/api/v1/scores", json=valid_score_body)
        finally:
            MockDatabaseMiddleware.__call__ = original_call
        
        assert response.status_code == 404
        data = response.json()
        assert f"There is no leaderboard with beatmap ID '{self.TEST_BEATMAP_ID}' and snapshot ID '1'" in data["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_admin_duplicate_score(self, TestClient, valid_score_body):
        """Test score submission fails when duplicate exists (integration)."""
        from app.test_app import MockDatabaseMiddleware
        
        mock_db = AsyncMock()
        mock_db.get.side_effect = [
            MagicMock(id=self.TEST_USER_ID),
            MagicMock(id=self.TEST_BEATMAP_ID),
            MagicMock(id=1, beatmap_id=self.TEST_BEATMAP_ID, snapshot_number=1),
            MagicMock(id=1, beatmap_id=self.TEST_BEATMAP_ID, beatmap_snapshot_id=1),
            MagicMock(id=1, user_id=self.TEST_USER_ID, beatmap_id=self.TEST_BEATMAP_ID),
        ]
        
        original_call = MockDatabaseMiddleware.__call__
        
        async def patched_call(self, scope, receive, send):
            scope["state"]["db"] = mock_db
            await self.app(scope, receive, send)
        
        MockDatabaseMiddleware.__call__ = patched_call
        
        try:
            response = TestClient.post("/api/v1/scores", json=valid_score_body)
        finally:
            MockDatabaseMiddleware.__call__ = original_call
        
        assert response.status_code == 409
        data = response.json()
        assert "already exists" in data["detail"]
