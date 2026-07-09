from ast import literal_eval
from datetime import datetime
from typing import Optional

from pydantic.main import BaseModel
from pydantic.fields import computed_field


class QueueRequestValidationTask(BaseModel):
    """Represents a queued request validation task for Tier 3 validators."""
    request_id: int
    queue_id: int
    beatmapset_id: int
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

    @computed_field
    @property
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
    def deserialize(cls, serialized_dict: dict[str, str]) -> "QueueRequestValidationTask":
        deserialized_dict = {}

        for key, value in serialized_dict.items():
            match key:
                case "request_id" | "queue_id" | "beatmapset_id":
                    value = int(value)
                case "completed_at" | "failed_at":
                    value = datetime.fromisoformat(value) if value else None

            deserialized_dict[key] = value

        return cls.model_validate(deserialized_dict)
