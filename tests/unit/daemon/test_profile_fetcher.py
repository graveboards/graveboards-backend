import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from app.daemon.services.profile_fetcher import ProfileFetcher
from app.database.models import ProfileFetcherTask, User, Profile
from app.exceptions import RedisLockTimeoutError


class TestProfileFetcher:
    """Test ProfileFetcher service."""

    @pytest.fixture
    def service(self):
        """Create a test ProfileFetcher instance."""
        rc = MagicMock()
        db = MagicMock()
        service = ProfileFetcher(rc, db)
        service._load_job = AsyncMock()
        return service

    async def test_preload_jobs_skips_disabled_tasks(self, service):
        """Test that disabled tasks are skipped during preload."""
        task1 = ProfileFetcherTask(id=1, user_id=123, enabled=True)
        task2 = ProfileFetcherTask(id=2, user_id=456, enabled=False)
        service._db.get_many = AsyncMock(return_value=[task1, task2])
        service._db.get = AsyncMock(side_effect=[None])

        await service._preload_jobs()

        assert service._load_job.call_count == 1

    async def test_execute_job_raises_value_error_when_record_not_found(self, service):
        """Test that _execute_job raises ValueError when task not found."""
        service._db.get = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="not found"):
            await service._execute_job(123)

    async def test_execute_job_skips_when_lock_not_acquired(self, service):
        """Test that execution is skipped when Redis lock is already held."""
        task = ProfileFetcherTask(id=1, user_id=123, enabled=True)
        service._db.get = AsyncMock(return_value=task)
        service._rc.set = AsyncMock(return_value=None)

        await service._execute_job(123)

        service._db.get.assert_awaited_once_with(ProfileFetcherTask, id=123)

    async def test_execute_job_fetches_user_profile_when_lock_acquired(self, service):
        """Test that profile is fetched when Redis lock is acquired."""
        task = ProfileFetcherTask(id=1, user_id=123, enabled=True)
        service._db.get = AsyncMock(return_value=task)
        service._rc.set = AsyncMock(return_value=True)
        service._rc.lock_ctx = MagicMock()
        service._rc.lock_ctx.__enter__ = MagicMock()
        service._rc.lock_ctx.__exit__ = MagicMock()
        service._respect_rate_limit = AsyncMock()
        service._oac.get_user = AsyncMock(return_value={"id": 123, "username": "test"})
        service._db.add = AsyncMock()

        with patch("app.daemon.services.profile_fetcher.ProfileSchema") as mock_schema:
            mock_schema.model_validate.return_value.model_dump.return_value = {
                "user_id": 123,
                "username": "test",
                "avatar_url": "http://test.com",
            }
            await service._execute_job(123)

        service._oac.get_user.assert_awaited_once_with(123)

    async def test_execute_job_creates_new_profile_when_not_exists(self, service):
        """Test that new profile is created when user has no profile."""
        task = ProfileFetcherTask(id=1, user_id=123, enabled=True)
        service._db.get = AsyncMock(side_effect=[
            task,
            None,
        ])
        service._rc.set = AsyncMock(return_value=True)
        service._respect_rate_limit = AsyncMock()
        service._oac.get_user = AsyncMock(return_value={"id": 123, "username": "test"})
        service._db.add = AsyncMock()

        with patch("app.daemon.services.profile_fetcher.ProfileSchema") as mock_schema:
            mock_schema.model_validate.return_value.model_dump.return_value = {
                "user_id": 123,
                "username": "test",
                "avatar_url": "http://test.com",
            }
            await service._execute_job(123)

        service._db.add.assert_awaited_once()

    async def test_auto_retry_decorator_applied(self, service):
        """Test that _execute_job has auto_retry decorator."""
        import inspect

        assert hasattr(service._execute_job, "__wrapped__")
