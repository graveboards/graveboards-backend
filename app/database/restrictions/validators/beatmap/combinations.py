from __future__ import annotations

from typing import Any

from app.database.restrictions.base import BeatmapRestrictionBase
from app.database.restrictions.context import ExecutionContext
from app.database.restrictions.exceptions import RestrictionViolationError


COMBINATION_TEMPLATES: dict[str, dict[str, Any]] = {
    "any": {
        "operator": "and",
        "rules": [],
    },
}


class CombinationRestriction(BeatmapRestrictionBase):
    restriction_type = "beatmap_combination"

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        combination_name = config.get("combination")

        if not combination_name:
            raise RestrictionViolationError(
                self.restriction_type,
                "Combination name is required",
            )

        template = COMBINATION_TEMPLATES.get(combination_name)
        if template is None:
            available = ", ".join(sorted(COMBINATION_TEMPLATES.keys()))
            raise RestrictionViolationError(
                self.restriction_type,
                f"Unknown combination '{combination_name}'. Available: {available}",
            )
