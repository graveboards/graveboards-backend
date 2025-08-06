from ast import literal_eval
from datetime import datetime

from app.database.schemas.sub_schemas import BeatmapOsuApiSchema


class Beatmap(BeatmapOsuApiSchema):
    def serialize(self) -> dict[str, str]:
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
    def deserialize(cls, serialized_dict: dict[str, str]) -> "Beatmap":
        deserialized_dict = {}

        for key, value in serialized_dict.items():
            match key:
                case "id" | "user_id" | "count_circles" | "count_sliders" | "count_spinners" | "hit_length" | "max_combo" | "mode_int" | "passcount" | "playcount" | "ranked" | "total_length":
                    value = int(value)
                case "accuracy" | "ar" | "bpm" | "cs" | "difficulty_rating" | "drain":
                    value = float(value)
                case (
                    "is_scoreable" |  # Bools
                    "failtimes" | "owners" | "top_tag_ids"  # Lists
                ):
                    value = literal_eval(value)
                case "deleted_at" | "last_updated":
                    value = datetime.fromisoformat(value) if value else None

            deserialized_dict[key] = value

        return cls.model_validate(deserialized_dict)
