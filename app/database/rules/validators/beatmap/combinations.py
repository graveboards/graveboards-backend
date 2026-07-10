from __future__ import annotations

from typing import Any

from app.database.rules.base import BeatmapRestrictionBase
from app.database.rules.context import ExecutionContext
from app.database.rules.exceptions import RuleViolationError


COMBINATION_TEMPLATES: dict[str, dict[str, Any]] = {
    "any": {
        "operator": "and",
        "rules": [],
    },
}


class CombinationRestriction(BeatmapRestrictionBase):
    type = "beatmap_combination"

    async def check_beatmap(self, context: ExecutionContext) -> None:
        config = context.config
        combination_name = config.get("combination")

        if not combination_name:
            raise RuleViolationError(
                self.type,
                "Combination name is required",
            )

        template = COMBINATION_TEMPLATES.get(combination_name)
        if template is None:
            available = ", ".join(sorted(COMBINATION_TEMPLATES.keys()))
            raise RuleViolationError(
                self.type,
                f"Unknown combination '{combination_name}'. Available: {available}",
            )
