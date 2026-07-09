from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from pydantic import BaseModel, field_validator

from app.database.restrictions.base import DatabaseRestrictionBase
from app.database.restrictions.exceptions import RestrictionViolationError

if TYPE_CHECKING:
    from app.database.restrictions.context import ExecutionContext

logger = logging.getLogger(__name__)


class UniqueArtistTitleConfig(BaseModel):
    ruleset: str = "osu"
    normalize_versions: bool = True

    @field_validator("ruleset")
    @classmethod
    def validate_ruleset(cls, v: str) -> str:
        valid = {"osu", "taiko", "fruits", "mania"}
        if v not in valid:
            raise ValueError(f"ruleset must be one of {sorted(valid)}")
        return v


class UniqueArtistTitleRestriction(DatabaseRestrictionBase):
    restriction_type = "unique_artist_title"
    config_schema = UniqueArtistTitleConfig
    supported_versions = {"1.0"}

    _RULESET_TO_INT = {
        "osu": 2,
        "taiko": 3,
        "fruits": 0,
        "mania": 1,
    }

    async def check_database(self, context: ExecutionContext) -> None:
        config = UniqueArtistTitleConfig(**context.config)
        identity = await context.get_metadata("song_identity")

        if not identity.get("normalized_artist") or not identity.get("normalized_title"):
            raise RestrictionViolationError(
                self.restriction_type,
                "Could not resolve song identity for uniqueness check",
            )

        ruleset_int = self._RULESET_TO_INT.get(config.ruleset, 2)
        search_status = "ranked,approved,qualified,loved"

        results = await context.osu_client.search_beatmapsets(
            status=search_status,
            mode=ruleset_int,
        )

        beatmapsets = results.get("beatmapsets", [])

        from app.database.restrictions.validators.metadata.song_identity import _normalize_text

        normalized_artist = identity["normalized_artist"]
        normalized_title = identity["normalized_title"]

        for bs in beatmapsets:
            bs_artist = (bs.get("artist") or "").strip()
            bs_title = (bs.get("title") or "").strip()

            if not bs_artist or not bs_title:
                continue

            normalized_bs_artist = _normalize_text(bs_artist)
            normalized_bs_title = _normalize_text(bs_title)

            if (
                normalized_bs_artist == normalized_artist
                and normalized_bs_title == normalized_title
            ):
                existing_id = bs.get("beatmapset_id") or bs.get("id")
                raise RestrictionViolationError(
                    self.restriction_type,
                    f"Song '{identity['artist']} - {identity['title']}' already has a ranked request in this queue (beatmapset_id={existing_id})",
                )
