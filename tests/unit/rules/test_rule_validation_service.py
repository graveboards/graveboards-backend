import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.redis import ChannelName
from app.redis.models import QueueRequestValidationTask


class TestQueueRequestValidationTask:
    @pytest.mark.unit
    def test_serialization(self):
        task = QueueRequestValidationTask(
            request_id=42,
            queue_id=1,
            beatmapset_id=12345,
            http_request_id="abc123def456",
        )
        serialized = task.serialize()

        assert serialized["request_id"] == "42"
        assert serialized["queue_id"] == "1"
        assert serialized["beatmapset_id"] == "12345"
        assert serialized["http_request_id"] == "abc123def456"

    @pytest.mark.unit
    def test_deserialization(self):
        serialized = {
            "request_id": "42",
            "queue_id": "1",
            "beatmapset_id": "12345",
            "http_request_id": "abc123def456",
            "completed_at": "",
            "failed_at": "",
        }
        task = QueueRequestValidationTask.deserialize(serialized)

        assert task.request_id == 42
        assert task.queue_id == 1
        assert task.beatmapset_id == 12345
        assert task.http_request_id == "abc123def456"
        assert task.completed_at is None
        assert task.failed_at is None

    @pytest.mark.unit
    def test_hashed_id_is_deterministic(self):
        task1 = QueueRequestValidationTask(
            request_id=42,
            queue_id=1,
            beatmapset_id=12345,
        )
        task2 = QueueRequestValidationTask(
            request_id=42,
            queue_id=1,
            beatmapset_id=12345,
        )

        assert task1.hashed_id == task2.hashed_id

    @pytest.mark.unit
    def test_roundtrip_serialization(self):
        task = QueueRequestValidationTask(
            request_id=42,
            queue_id=1,
            beatmapset_id=12345,
            http_request_id="abc123def456",
        )
        serialized = task.serialize()
        deserialized = QueueRequestValidationTask.deserialize(serialized)

        assert deserialized.request_id == task.request_id
        assert deserialized.queue_id == task.queue_id
        assert deserialized.beatmapset_id == task.beatmapset_id
        assert deserialized.http_request_id == task.http_request_id


class TestValidationChannel:
    @pytest.mark.unit
    def test_channel_name_exists(self):
        assert hasattr(ChannelName, "QUEUE_REQUEST_VALIDATION_TASKS")

    @pytest.mark.unit
    def test_channel_name_value(self):
        assert ChannelName.QUEUE_REQUEST_VALIDATION_TASKS == "queue_request_validation_tasks"
