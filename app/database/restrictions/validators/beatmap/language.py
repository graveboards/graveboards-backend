from __future__ import annotations

from app.database.restrictions.base import BeatmapRestrictionBase
from app.database.restrictions.context import ExecutionContext
from app.database.restrictions.exceptions import RestrictionViolationError
from app.database.schemas.restriction import LanguageConfig


class LanguageRestriction(BeatmapRestrictionBase):
    restriction_type = "beatmap_language"
    config_schema = LanguageConfig

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        logic = config.get("logic", "any")
        beatmapset = context.beatmapset

        if beatmapset is None or beatmapset.language is None:
            raise RestrictionViolationError(
                self.restriction_type,
                "Beatmapset language is not available",
            )

        allowed_ids = set(config.get("language_ids", []))
        actual_id = beatmapset.language.id

        if logic == "all":
            if actual_id not in allowed_ids:
                raise RestrictionViolationError(
                    self.restriction_type,
                    f"Beatmapset language ({actual_id}) is not in the allowed "
                    f"languages: {sorted(allowed_ids)}",
                )
        else:
            if actual_id not in allowed_ids:
                raise RestrictionViolationError(
                    self.restriction_type,
                    f"Beatmapset language ({actual_id}) is not in the allowed "
                    f"languages: {sorted(allowed_ids)}",
                )
