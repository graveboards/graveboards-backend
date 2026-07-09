from __future__ import annotations

from app.database.restrictions.base import BeatmapRestrictionBase
from app.database.restrictions.context import ExecutionContext
from app.database.restrictions.exceptions import RestrictionViolationError
from app.database.schemas.restriction import GenreConfig


class GenreRestriction(BeatmapRestrictionBase):
    restriction_type = "beatmap_genre"
    config_schema = GenreConfig

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        logic = config.get("logic", "any")
        beatmapset = context.beatmapset

        if beatmapset is None or beatmapset.genre is None:
            raise RestrictionViolationError(
                self.restriction_type,
                "Beatmapset genre is not available",
            )

        allowed_ids = set(config.get("genre_ids", []))
        actual_id = beatmapset.genre.id

        if logic == "all":
            if actual_id not in allowed_ids:
                raise RestrictionViolationError(
                    self.restriction_type,
                    f"Beatmapset genre ({actual_id}) is not in the allowed "
                    f"genres: {sorted(allowed_ids)}",
                )
        else:
            if actual_id not in allowed_ids:
                raise RestrictionViolationError(
                    self.restriction_type,
                    f"Beatmapset genre ({actual_id}) is not in the allowed "
                    f"genres: {sorted(allowed_ids)}",
                )
