from __future__ import annotations
from datetime import datetime
from typing import Any
from typing import cast as typing_cast

from pydantic.fields import computed_field
from pydantic.main import BaseModel


class QueueRequestValidationTask(BaseModel):
    """Represents a queued request validation task for Tier 3 validators."""

    request_id: int
    queue_id: int
    beatmapset_id: int
    http_request_id: str = ""
    rules_snapshot: str = ""
    completed_at: datetime | None = None
    failed_at: datetime | None = None

    @computed_field
    def hashed_id(self) -> int:
        return hash(("validation", self.request_id)) & 0x7FFFFFFFFFFFFFFF

    def serialize(self) -> dict[str, str]:
        serialized_dict = {}

        for key, value in self.__dict__.items():
            match key:
                case "completed_at" | "failed_at":
                    value = value.isoformat() if value is not None else ""

            serialized_dict[key] = str(value)

        return serialized_dict

    @classmethod
    def deserialize(cls, serialized_dict: dict[str | bytes, str | bytes]) -> QueueRequestValidationTask:
        string_dict = {str(k): str(v) for k, v in serialized_dict.items()}
        deserialized_dict: dict[str, Any] = {}

        for key, value in string_dict.items():
            match key:
                case "request_id" | "queue_id" | "beatmapset_id":
                    deserialized_dict[key] = int(value)
                case "completed_at" | "failed_at":
                    deserialized_dict[key] = datetime.fromisoformat(value) if value else None
                case _:
                    deserialized_dict[key] = value

        return cls.model_validate(deserialized_dict)
