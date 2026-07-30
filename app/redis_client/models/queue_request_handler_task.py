from __future__ import annotations
from ast import literal_eval
from datetime import datetime
from typing import Any
from typing import cast as typing_cast

from pydantic.fields import computed_field
from pydantic.main import BaseModel


class QueueRequestHandlerTask(BaseModel):
    """Represents a queued beatmapset request processing task."""

    user_id: int
    beatmapset_id: int
    queue_id: int
    comment: str
    mv_checked: bool
    http_request_id: str = ""
    completed_at: datetime | None = None
    failed_at: datetime | None = None

    @computed_field
    def hashed_id(self) -> int:
        """Compute a stable positive hash identifier for the task.

        Returns:
            A 64-bit positive integer hash.
        """
        return hash((self.queue_id, self.beatmapset_id)) & 0x7FFFFFFFFFFFFFFF

    def serialize(self) -> dict[str, str]:
        """Serialize the task for Redis storage.

        Returns:
            A dictionary with stringified values.
        """
        serialized_dict = {}

        for key, value in self.__dict__.items():
            match key:
                case "completed_at" | "failed_at":
                    value = value.isoformat() if value is not None else ""

            serialized_dict[key] = str(value)

        return serialized_dict

    @classmethod
    def deserialize(cls, serialized_dict: dict[str | bytes, str | bytes]) -> QueueRequestHandlerTask:
        """Deserialize a stored task dictionary from Redis.

        Args:
            serialized_dict:
                Serialized task data (keys and values may be bytes or str).

        Returns:
            A validated ``QueueRequestHandlerTask`` instance.
        """
        string_dict = {str(k): str(v) for k, v in serialized_dict.items()}
        deserialized_dict: dict[str, Any] = {}

        for key, value in string_dict.items():
            match key:
                case "user_id" | "beatmapset_id" | "queue_id":
                    deserialized_dict[key] = int(value)
                case "mv_checked":
                    deserialized_dict[key] = literal_eval(value)
                case "completed_at" | "failed_at":
                    deserialized_dict[key] = datetime.fromisoformat(value) if value else None
                case _:
                    deserialized_dict[key] = value

        return typing_cast(QueueRequestHandlerTask, cls.model_validate(deserialized_dict))
