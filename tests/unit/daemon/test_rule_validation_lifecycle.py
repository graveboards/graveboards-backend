from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.daemon.services.rule_validation import RuleValidationService
from app.exceptions import JobAbortedError
from app.redis_client import TASK_RETENTION_SECONDS
from app.redis_client.models import QueueRequestValidationTask


class TestRuleValidationTaskLifecycle:
    """Terminal task hashes are stamped, then left to expire."""

    @pytest.fixture
    def service(self) -> RuleValidationService:
        rc = MagicMock()
        rc.hgetall = AsyncMock()
        rc.hset = AsyncMock()
        rc.expire = AsyncMock()
        rc.publish = AsyncMock()
        return RuleValidationService(rc, MagicMock())

    @staticmethod
    def _serialized_record() -> dict[str, str]:
        return QueueRequestValidationTask(
            request_id=1, queue_id=2, beatmapset_id=3, rules_snapshot="[]"
        ).serialize()

    async def test_aborts_without_marking_a_missing_record(
        self, service: RuleValidationService
    ) -> None:
        service._rc.hgetall.return_value = {}

        with pytest.raises(JobAbortedError):
            await service._execute_job(123)

        service._rc.hset.assert_not_awaited()
        service._rc.expire.assert_not_awaited()

    async def test_failure_marks_failed_at_and_starts_retention(
        self, service: RuleValidationService
    ) -> None:
        service._rc.hgetall.return_value = self._serialized_record()

        osu_client = MagicMock()
        osu_client.__aenter__ = AsyncMock(return_value=MagicMock())
        osu_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "app.daemon.services.rule_validation.OsuAPIClient",
                return_value=osu_client,
            ),
            patch.object(service, "_run_validation", AsyncMock(side_effect=RuntimeError("boom"))),
            pytest.raises(RuntimeError, match="boom"),
        ):
            await service._execute_job(123)

        service._rc.hset.assert_awaited()
        service._rc.expire.assert_awaited_once_with(
            "queue_request_handler_task:123", TASK_RETENTION_SECONDS
        )
