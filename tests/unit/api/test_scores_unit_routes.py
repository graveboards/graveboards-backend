"""
Unit tests for POST /api/v1/scores endpoint (admin-only).

Tests the score submission logic with mocked dependencies (fast, isolated).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock


class TestScoresPostUnit:
    """Unit tests for POST /api/v1/scores endpoint."""

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

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_admin_submission_creates_score(self, valid_score_body):
        """Test that admin can submit a new score."""
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
        
        from api.v1.scores import post
        
        result = await post(body=valid_score_body, db=mock_db)
        
        assert result[1] == 201
        assert result[0]["message"] == "Score added successfully!"
        assert mock_db.add.called

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_admin_submission_user_not_found(self, valid_score_body):
        """Test that score submission fails when user doesn't exist."""
        mock_db = AsyncMock()
        mock_db.get.side_effect = [None]
        
        from api.v1.scores import post
        from app.exceptions import NotFound
        
        try:
            await post(body=valid_score_body, db=mock_db)
            assert False, "Expected NotFound exception"
        except NotFound as e:
            assert f"There is no user with ID '{self.TEST_USER_ID}'" in str(e)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_admin_submission_beatmap_not_found(self, valid_score_body):
        """Test that score submission fails when beatmap doesn't exist."""
        mock_db = AsyncMock()
        mock_db.get.side_effect = [
            MagicMock(id=self.TEST_USER_ID),
            None,
        ]
        
        from api.v1.scores import post
        from app.exceptions import NotFound
        
        try:
            await post(body=valid_score_body, db=mock_db)
            assert False, "Expected NotFound exception"
        except NotFound as e:
            assert f"There is no beatmap with ID '{self.TEST_BEATMAP_ID}'" in str(e)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_admin_submission_beatmap_snapshot_not_found(self, valid_score_body):
        """Test that score submission fails when beatmap snapshot doesn't exist."""
        mock_db = AsyncMock()
        mock_db.get.side_effect = [
            MagicMock(id=self.TEST_USER_ID),
            MagicMock(id=self.TEST_BEATMAP_ID),
            None,
        ]
        
        from api.v1.scores import post
        from app.exceptions import NotFound
        
        try:
            await post(body=valid_score_body, db=mock_db)
            assert False, "Expected NotFound exception"
        except NotFound as e:
            assert f"There is no beatmap snapshot with beatmap ID '{self.TEST_BEATMAP_ID}'" in str(e)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_admin_submission_leaderboard_not_found(self, valid_score_body):
        """Test that score submission fails when leaderboard doesn't exist."""
        mock_db = AsyncMock()
        
        mock_user = MagicMock()
        mock_user.id = self.TEST_USER_ID
        mock_beatmap = MagicMock()
        mock_beatmap.id = self.TEST_BEATMAP_ID
        mock_snapshot = MagicMock()
        mock_snapshot.id = 1
        mock_snapshot.beatmap_id = self.TEST_BEATMAP_ID
        
        mock_db.get.side_effect = [
            mock_user,
            mock_beatmap,
            mock_snapshot,
            None,
        ]
        
        from api.v1.scores import post
        from app.exceptions import NotFound
        
        try:
            await post(body=valid_score_body, db=mock_db)
            assert False, "Expected NotFound exception"
        except NotFound as e:
            assert f"There is no leaderboard with beatmap ID '{self.TEST_BEATMAP_ID}' and snapshot ID '1'" in str(e)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_admin_submission_duplicate_score(self, valid_score_body):
        """Test that score submission fails when duplicate exists."""
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
        mock_duplicate_score = MagicMock()
        mock_duplicate_score.id = 1
        
        mock_db.get.side_effect = [
            mock_user,
            mock_beatmap,
            mock_snapshot,
            mock_leaderboard,
            mock_duplicate_score,
        ]
        
        from api.v1.scores import post
        from app.exceptions import Conflict
        
        try:
            await post(body=valid_score_body, db=mock_db)
            assert False, "Expected Conflict exception"
        except Conflict as e:
            assert "already exists" in str(e)
