import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from app.daemon.services.score_fetcher import ScoreFetcher
from app.database.models import ScoreFetcherTask, Leaderboard


class TestScoreFetcher:
    """Test ScoreFetcher service (incomplete implementation)."""

    @pytest.fixture
    def service(self):
        """Create a test ScoreFetcher instance."""
        rc = MagicMock()
        db = MagicMock()
        return ScoreFetcher(rc, db)

    async def test_preload_jobs_schedules_enabled_tasks(self, service):
        """Test that preload_jobs schedules enabled score fetch tasks."""
        task1 = ScoreFetcherTask(id=1, user_id=123, enabled=True, last_fetch=None)
        task2 = ScoreFetcherTask(id=2, user_id=456, enabled=False, last_fetch=None)
        service._db.get_many = AsyncMock(return_value=[task1, task2])
        service._load_job = AsyncMock()

        await service._preload_jobs()

        assert service._load_job.call_count == 1

    async def test_preload_jobs_skips_disabled_tasks(self, service):
        """Test that disabled score fetch tasks are skipped."""
        task = ScoreFetcherTask(id=1, user_id=123, enabled=False)
        service._db.get_many = AsyncMock(return_value=[task])
        service._load_job = AsyncMock()

        await service._preload_jobs()

        service._load_job.assert_not_called()

    async def test_auto_retry_decorator_applied(self, service):
        """Test that _execute_job has auto_retry decorator."""
        import inspect

        assert hasattr(service._execute_job, "__wrapped__")

    async def test_score_is_submittable_checks_leaderboard(self, service):
        """Test that _score_is_submittable checks for active leaderboard."""
        score = {
            "beatmap": {
                "id": 456
            }
        }
        service._db.get = AsyncMock(return_value=MagicMock())

        result = await service._score_is_submittable(score)

        service._db.get.assert_awaited_once_with(Leaderboard, beatmap_id=456)
        assert result is True

    async def test_score_is_submittable_returns_false_without_leaderboard(self, service):
        """Test that _score_is_submittable returns False without leaderboard."""
        score = {
            "beatmap": {
                "id": 456
            }
        }
        service._db.get = AsyncMock(return_value=None)

        result = await service._score_is_submittable(score)

        assert result is False
