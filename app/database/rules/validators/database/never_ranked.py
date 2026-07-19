from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from pydantic import BaseModel, field_validator

from app.database.rules.base import DatabaseRestrictionBase
from app.database.rules.exceptions import RuleViolationError
from app.database.rules.validators.metadata.song_identity import normalized_identity_forms
from app.osu_api.enums import Ruleset

if TYPE_CHECKING:
    from app.database.rules.context import ExecutionContext

logger = logging.getLogger(__name__)


class NeverRankedConfig(BaseModel):
    ruleset: str = "osu"
    normalize_versions: bool = True

    @field_validator("ruleset")
    @classmethod
    def validate_ruleset(cls, v: str) -> str:
        valid = {"osu", "taiko", "fruits", "mania"}
        if v not in valid:
            raise ValueError(f"ruleset must be one of {sorted(valid)}")
        return v


class NeverRankedRestriction(DatabaseRestrictionBase):
    type = "never_ranked"
    config_schema = NeverRankedConfig
    supported_versions = {"1.0"}

    _MAX_SEARCH_PAGES = 5

    async def check_database(self, context: ExecutionContext) -> None:
        config = NeverRankedConfig(**context.config)
        identity = await context.get_metadata("song_identity")

        candidate_forms = normalized_identity_forms(
            identity.get("artist", ""),
            identity.get("title", ""),
            identity.get("artist_unicode", ""),
            identity.get("title_unicode", ""),
            strip_version_markers=config.normalize_versions,
        )
        if not candidate_forms:
            raise RuleViolationError(
                self.type,
                "Could not resolve song identity for ranking check",
            )

        mode_int = Ruleset.to_mode_int(config.ruleset)
        search_status = "ranked,approved,qualified,loved"
        text_query = " ".join(
            part for part in (identity.get("artist", ""), identity.get("title", "")) if part
        ).strip()

        for page in range(1, self._MAX_SEARCH_PAGES + 1):
            results = await context.osu_client.search_beatmapsets(
                status=search_status,
                mode=mode_int,
                query=text_query or None,
                page=page,
            )
            beatmapsets = results.get("beatmapsets", [])
            if not beatmapsets:
                break

            for bs in beatmapsets:
                bs_forms = normalized_identity_forms(
                    bs.get("artist", ""),
                    bs.get("title", ""),
                    bs.get("artist_unicode", ""),
                    bs.get("title_unicode", ""),
                    strip_version_markers=config.normalize_versions,
                )
                if candidate_forms & bs_forms:
                    raise RuleViolationError(
                        self.type,
                        f"Song '{identity['artist']} - {identity['title']}' is "
                        f"already ranked on osu! {config.ruleset}",
                    )
