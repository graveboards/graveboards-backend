from ast import literal_eval
from datetime import datetime
from typing import Optional

from pydantic.main import BaseModel
from pydantic.fields import computed_field


class QueueRequestHandlerTask(BaseModel):
    """Represents a queued beatmapset request processing task."""
    user_id: int
    beatmapset_id: int
    queue_id: int
    comment: str
    mv_checked: bool
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

    @computed_field
    @property
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
    def deserialize(cls, serialized_dict: dict[str, str]) -> "QueueRequestHandlerTask":
        """Deserialize a stored task dictionary.

        Args:
            serialized_dict:
                Serialized task data.

        Returns:
            A validated ``QueueRequestHandlerTask`` instance.
        """
        deserialized_dict = {}

        for key, value in serialized_dict.items():
            match key:
                case "user_id" | "beatmapset_id" | "queue_id":
                    value = int(value)
                case "mv_checked":
                    value = literal_eval(value)
                case "completed_at" | "failed_at":
                    value = datetime.fromisoformat(value) if value else None

            deserialized_dict[key] = value

        return cls.model_validate(deserialized_dict)
