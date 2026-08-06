"""Beatmapset genre restriction for ranked-beatmap submission."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from app.database.rules.base import BeatmapRestrictionBase
from app.database.rules.exceptions import RuleViolationError
from app.database.schemas.rule import GenreConfig

if TYPE_CHECKING:
    from app.database.rules.context import ExecutionContext


class GenreRestriction(BeatmapRestrictionBase):
    """Require the beatmapset genre to be one of the allowed genre ids."""

    type = "beatmap_genre"
    config_schema = GenreConfig

    @override
    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        beatmapset = context.beatmapset

        if beatmapset is None or beatmapset.genre is None:
            raise RuleViolationError(
                self.type,
                "Beatmapset genre is not available",
            )

        allowed_ids = set(config.get("genre_ids", []))
        actual_id = beatmapset.genre.id

        if actual_id not in allowed_ids:
            raise RuleViolationError(
                self.type,
                f"Beatmapset genre ({actual_id}) is not in the allowed "
                f"genres: {sorted(allowed_ids)}",
            )
