from __future__ import annotations

from app.database.restrictions.base import BeatmapRestrictionBase
from app.database.restrictions.context import ExecutionContext
from app.database.restrictions.exceptions import RestrictionViolationError
from app.database.schemas.restriction import TagsConfig


class TagsRestriction(BeatmapRestrictionBase):
    restriction_type = "beatmap_tags"
    config_schema = TagsConfig

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        logic = config.get("logic", "any")
        beatmaps = context.beatmaps or []
        beatmapset = context.beatmapset

        required_tag_ids = set(config.get("tag_ids", []))
        if not required_tag_ids:
            return

        beatmap_tag_ids: set[int] = set()
        for bm in beatmaps:
            if bm.top_tag_ids:
                for tag in bm.top_tag_ids:
                    tag_id = tag.get("tag_id") if isinstance(tag, dict) else None
                    if tag_id is not None:
                        beatmap_tag_ids.add(tag_id)

        if not beatmap_tag_ids and beatmapset:
            if beatmapset.tags:
                for tag_str in beatmapset.tags.split(","):
                    tag_str = tag_str.strip()
                    if tag_str:
                        try:
                            beatmap_tag_ids.add(int(tag_str))
                        except (ValueError, TypeError):
                            pass

        if logic == "all":
            missing = required_tag_ids - beatmap_tag_ids
            if missing:
                raise RestrictionViolationError(
                    self.restriction_type,
                    f"Beatmapset is missing required tags: {sorted(missing)}. "
                    f"Available tags: {sorted(beatmap_tag_ids)}",
                )
        else:
            if not beatmap_tag_ids.intersection(required_tag_ids):
                raise RestrictionViolationError(
                    self.restriction_type,
                    f"Beatmapset does not have any of the required tags: "
                    f"{sorted(required_tag_ids)}. Available tags: "
                    f"{sorted(beatmap_tag_ids)}",
                )
