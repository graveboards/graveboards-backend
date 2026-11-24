from unittest.mock import AsyncMock, MagicMock

import pytest

from app.daemon.services.service.scheduled import ScheduledService
from app.exceptions import JobAbortedError
from app.utils import aware_utcnow


class _ScheduledService(ScheduledService):
    """Minimal rescheduling service whose job body is supplied per test."""

    LOGGER = MagicMock()
    CHANNEL = "test-channel"
    JOB_NAME = "test"

    async def _execute_job(self, job_id: int) -> None:
        await self.job_body(job_id)


class TestScheduledService:
    """Test scheduled job execution and rescheduling."""

    @pytest.fixture
    def service(self) -> _ScheduledService:
        service = _ScheduledService(MagicMock(), MagicMock())
        service.job_body = AsyncMock()
        service.logger = MagicMock()
        return service

    async def test_failed_job_is_rescheduled(self, service: _ScheduledService) -> None:
        """Test that a failing job stays in the queue for another attempt."""
        service.job_body.side_effect = RuntimeError("transient")

        await service._handle_job(7, aware_utcnow())

        assert [job_id for _, job_id in service._job_heap] == [7]

    async def test_aborted_job_is_not_rescheduled(self, service: _ScheduledService) -> None:
        """Test that a job signalling JobAbortedError is dropped from the queue."""
        service.job_body.side_effect = JobAbortedError("record 7 not found")

        await service._handle_job(7, aware_utcnow())

        assert service._job_heap == []
        assert 7 not in service._active_job_ids

    async def test_aborted_job_logs_without_traceback(self, service: _ScheduledService) -> None:
        """Test that an abort is reported as a warning rather than an exception."""
        service.job_body.side_effect = JobAbortedError("record 7 not found")

        await service._handle_job(7, aware_utcnow())

        service.logger.warning.assert_called_once()
        service.logger.exception.assert_not_called()
