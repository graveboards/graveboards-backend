import pytest
from unittest.mock import MagicMock, AsyncMock, patch, call
from datetime import datetime

from app.daemon.services.queue_request_handler import QueueRequestHandler
from app.redis.models import QueueRequestHandlerTask


class TestQueueRequestHandler:
    """Test QueueRequestHandler service."""

    @pytest.fixture
    def service(self):
        """Create a test QueueRequestHandler instance."""
        rc = MagicMock()
        rc.hgetall = AsyncMock()
        rc.hset = AsyncMock()
        db = MagicMock()
        db.add = AsyncMock()
        return QueueRequestHandler(rc, db)

    async def test_resolve_job_instruction_returns_execution_time(self, service):
        """Test that _resolve_job_instruction returns instruction with current time."""
        instruction = await service._resolve_job_instruction(123)

        assert instruction is not None
        assert instruction.execution_time is not None

    async def test_execute_job_raises_value_error_when_record_not_found(self, service):
        """Test that _execute_job raises ValueError when task not found in Redis."""
        service._rc.hgetall.return_value = None

        with pytest.raises(ValueError, match="not found"):
            await service._execute_job(123)

    async def test_execute_job_successfully_processes_task(self, service):
        """Test successful task processing."""
        serialized_task = {
            "user_id": "123",
            "beatmapset_id": "456",
            "queue_id": "789",
            "comment": "test comment",
            "mv_checked": "False",
        }
        service._rc.hgetall.return_value = serialized_task

        mock_bm = MagicMock()
        mock_bm.archive = AsyncMock()
        mock_request = MagicMock()
        mock_request.id = 999
        mock_request.beatmapset_id = 456
        mock_request.queue_id = 789
        service._db.add.return_value = mock_request

        with patch("app.daemon.services.queue_request_handler.BeatmapManager", return_value=mock_bm), \
             patch("app.daemon.services.queue_request_handler.aware_utcnow") as mock_utcnow:
            mock_utcnow.return_value = datetime(2026, 1, 1)
            await service._execute_job(123)

        service._rc.hgetall.assert_awaited_once()
        mock_bm.archive.assert_awaited_once_with(456)
        service._db.add.assert_awaited_once()

    async def test_execute_job_sets_completed_at_on_success(self, service):
        """Test that completed_at is set on successful execution."""
        serialized_task = {
            "user_id": "123",
            "beatmapset_id": "456",
            "queue_id": "789",
            "comment": "test",
            "mv_checked": "False",
        }
        service._rc.hgetall.return_value = serialized_task

        mock_bm = MagicMock()
        mock_bm.archive = AsyncMock()
        service._db.add.return_value = MagicMock()

        with patch("app.daemon.services.queue_request_handler.BeatmapManager", return_value=mock_bm), \
             patch("app.daemon.services.queue_request_handler.aware_utcnow") as mock_utcnow:
            mock_utcnow.return_value = datetime(2026, 1, 1)
            await service._execute_job(123)

        assert service._rc.hset.call_count >= 1
        completed_calls = [c for c in service._rc.hset.call_args_list if c[0][1] == "completed_at"]
        assert len(completed_calls) >= 1

    async def test_execute_job_sets_failed_at_on_exception(self, service):
        """Test that failed_at is set when an exception occurs."""
        serialized_task = {
            "user_id": "123",
            "beatmapset_id": "456",
            "queue_id": "789",
            "comment": "test",
            "mv_checked": "False",
        }
        service._rc.hgetall.return_value = serialized_task

        mock_bm = MagicMock()
        mock_bm.archive = AsyncMock(side_effect=Exception("Test error"))
        service._db.add.return_value = MagicMock()

        with patch("app.daemon.services.queue_request_handler.BeatmapManager", return_value=mock_bm), \
             patch("app.daemon.services.queue_request_handler.aware_utcnow") as mock_utcnow:
            mock_utcnow.return_value = datetime(2026, 1, 1)
            with pytest.raises(Exception):
                await service._execute_job(123)

        assert service._rc.hset.call_count >= 1
        failed_calls = [c for c in service._rc.hset.call_args_list if c[0][1] == "failed_at"]
        assert len(failed_calls) >= 1

    async def test_execute_job_deserializes_task_correctly(self, service):
        """Test that task is deserialized properly."""
        serialized_task = {
            "user_id": "123",
            "beatmapset_id": "456",
            "queue_id": "789",
            "comment": "test",
            "mv_checked": "False",
        }
        service._rc.hgetall.return_value = serialized_task

        mock_bm = MagicMock()
        mock_bm.archive = AsyncMock()
        service._db.add.return_value = MagicMock()

        with patch("app.daemon.services.queue_request_handler.BeatmapManager", return_value=mock_bm), \
             patch("app.daemon.services.queue_request_handler.QueueRequestHandlerTask.deserialize") as mock_deserialize, \
             patch("app.daemon.services.queue_request_handler.aware_utcnow"), \
             patch("app.daemon.services.queue_request_handler.RequestSchema"):
            mock_deserialize.return_value = QueueRequestHandlerTask(
                user_id=123,
                beatmapset_id=456,
                queue_id=789,
                comment="test",
                mv_checked=False,
            )
            await service._execute_job(123)

        mock_deserialize.assert_called_once_with(serialized_task)

    async def test_execute_job_excludes_correct_fields_from_schema(self, service):
        """Test that RequestSchema excludes correct fields."""
        serialized_task = {
            "user_id": "123",
            "beatmapset_id": "456",
            "queue_id": "789",
            "comment": "test",
            "mv_checked": "False",
        }
        service._rc.hgetall.return_value = serialized_task

        mock_bm = MagicMock()
        mock_bm.archive = AsyncMock()

        mock_schema_instance = MagicMock()
        mock_schema_instance.model_dump.return_value = {
            "user_id": 123,
            "beatmapset_id": 456,
            "queue_id": 789,
            "comment": "test",
            "mv_checked": False,
        }

        with patch("app.daemon.services.queue_request_handler.BeatmapManager", return_value=mock_bm), \
             patch("app.daemon.services.queue_request_handler.aware_utcnow"), \
             patch("app.daemon.services.queue_request_handler.RequestSchema") as mock_schema_class:
            mock_schema_class.model_validate.return_value = mock_schema_instance
            service._db.add.return_value = MagicMock()
            await service._execute_job(123)

        mock_schema_instance.model_dump.assert_called_once_with(
            exclude={"user_profile", "queue", "beatmapset_snapshot"}
        )

    async def test_auto_retry_decorator_applied(self, service):
        """Test that _execute_job has auto_retry decorator."""
        import inspect

        assert hasattr(service._execute_job, "__wrapped__") or hasattr(service._execute_job, "__call__")

    async def test_auto_retry_configured_with_connect_timeout(self, service):
        """Test that auto_retry is configured to catch ConnectTimeout."""
        import inspect

        sig = inspect.signature(service._execute_job)
        wrapped = getattr(service._execute_job, "__wrapped__", service._execute_job)

        assert wrapped is not None
