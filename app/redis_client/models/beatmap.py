from ast import literal_eval
from datetime import datetime
from typing import Any, cast as typing_cast

from app.database.schemas.sub_schemas import BeatmapOsuApiSchema


class Beatmap(BeatmapOsuApiSchema):
    """Domain model representing an osu! beatmap."""

    def serialize(self) -> dict[str, str]:
        """Serialize the beatmap into a Redis-safe string dictionary.

        Returns:
            A dictionary with stringified values.
        """
        serialized_dict = {}

        for key, value in self.__dict__.items():
            match key:
                case "deleted_at" | "last_updated":
                    value = value.isoformat() if value is not None else ""
                case "failtimes":
                    if isinstance(value, list):
                        value = [item.model_dump(mode="json") for item in value]
                    elif value is not None:
                        value = value.model_dump(mode="json")

            serialized_dict[key] = str(value) if value is not None else ""

        return serialized_dict

    @classmethod
    def deserialize(cls, serialized_dict: dict[str, str]) -> Beatmap:
        """Deserialize a Redis-stored beatmap dictionary.

        Args:
            serialized_dict:
                Serialized beatmap data.

        Returns:
            A validated ``Beatmap`` instance.
        """
        deserialized_dict: dict[str, Any] = {}

        for key, value in serialized_dict.items():
            match key:
                case "id" | "user_id" | "count_circles" | "count_sliders" | "count_spinners" | "hit_length" | "max_combo" | "mode_int" | "passcount" | "playcount" | "ranked" | "total_length":
                    deserialized_dict[key] = int(value) if value != "" else None
                case "accuracy" | "ar" | "bpm" | "cs" | "difficulty_rating" | "drain":
                    deserialized_dict[key] = float(value) if value != "" else None
                case "is_scoreable" | "failtimes" | "owners" | "top_tag_ids":
                    deserialized_dict[key] = literal_eval(value) if value != "" else None
                case "deleted_at" | "last_updated":
                    deserialized_dict[key] = datetime.fromisoformat(value) if value != "" else None

        return typing_cast(Beatmap, cls.model_validate(deserialized_dict))
