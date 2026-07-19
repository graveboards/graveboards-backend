from __future__ import annotations

from app.database.rules.base import BeatmapRestrictionBase
from app.database.rules.context import ExecutionContext
from app.database.rules.exceptions import RuleViolationError
from app.database.schemas.rule import TagsConfig


class TagsRestriction(BeatmapRestrictionBase):
    type = "beatmap_tags"
    config_schema = TagsConfig

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        logic = config.get("logic", "any")
        beatmaps = context.beatmaps or []

        required_tag_ids = set(config.get("tag_ids", []))
        if not required_tag_ids:
            return

        beatmap_tag_ids: set[int] = set()
        has_tag_metadata = False
        for bm in beatmaps:
            if bm.top_tag_ids:
                has_tag_metadata = True
                for tag in bm.top_tag_ids:
                    tag_id = tag.get("tag_id") if isinstance(tag, dict) else None
                    if tag_id is not None:
                        beatmap_tag_ids.add(tag_id)

        if not has_tag_metadata:
            raise RuleViolationError(
                self.type,
                "Tag metadata (top_tag_ids) is unavailable for this beatmapset, "
                "so the required-tags rule cannot be evaluated",
            )

        if logic == "all":
            missing = required_tag_ids - beatmap_tag_ids
            if missing:
                raise RuleViolationError(
                    self.type,
                    f"Beatmapset is missing required tags: {sorted(missing)}. "
                    f"Available tags: {sorted(beatmap_tag_ids)}",
                )
        else:
            if not beatmap_tag_ids.intersection(required_tag_ids):
                raise RuleViolationError(
                    self.type,
                    f"Beatmapset does not have any of the required tags: "
                    f"{sorted(required_tag_ids)}. Available tags: "
                    f"{sorted(beatmap_tag_ids)}",
                )
