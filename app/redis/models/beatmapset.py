from ast import literal_eval
from datetime import datetime

from app.database.schemas.sub_schemas import BeatmapsetOsuApiSchema
from .beatmap import Beatmap


class Beatmapset(BeatmapsetOsuApiSchema):
    """Domain model representing an osu! beatmapset and its beatmaps."""
    beatmaps: list["Beatmap"]

    def serialize(self) -> dict[str, str]:
        """Serialize the beatmapset into a Redis-safe string dictionary.

        Returns:
            A dictionary with stringified values.
        """
        serialized_dict = {}

        for key, value in self.__dict__.items():
            match key:
                case "deleted_at" | "last_updated" | "submitted_date" | "ranked_date":
                    value = value.isoformat() if value is not None else ""
                case "beatmaps":
                    value = [beatmap.serialize() for beatmap in value]
                case "availability" | "covers" | "current_nominations" | "description" | "genre" | "hype" | "language" | "nominations_summary":
                    if isinstance(value, list):
                        value = [item.model_dump(mode="json") for item in value]
                    elif value is not None:
                        value = value.model_dump(mode="json")

            serialized_dict[key] = str(value) if value is not None else ""

        return serialized_dict

    @classmethod
    def deserialize(cls, serialized_dict: dict[str, str]) -> "Beatmapset":
        """Deserialize a Redis-stored beatmapset dictionary.

        Args:
            serialized_dict:
                Serialized beatmapset data.

        Returns:
            A validated ``Beatmapset`` instance.
        """
        deserialized_dict = {}

        for key, value in serialized_dict.items():
            match key:
                case "id" | "user_id" | "favourite_count" | "offset" | "play_count" | "ranked" | "track_id":
                    value = int(value) if value != "" else None
                case "bpm" | "rating":
                    value = float(value)
                case (
                    "verified" | "nsfw" | "video" | "is_scoreable" | "spotlight" | "discussion_enabled" | "discussion_locked" | "can_be_hyped" | "storyboard" |  # Bools
                    "availability" | "description" | "nominations_summary" | "user" | "covers" | "genre" | "hype" | "language" |  # Dicts
                    "pack_tags" | "current_nominations" | "ratings"  # Lists
                ):
                    value = literal_eval(value) if value != "" else None
                case "deleted_at" | "last_updated" | "submitted_date" | "ranked_date":
                    value = datetime.fromisoformat(value) if value != "" else None
                case "beatmaps":
                    value = [Beatmap.deserialize(beatmap) for beatmap in literal_eval(value)]

            deserialized_dict[key] = value

        return cls.model_validate(deserialized_dict)
