"""Named combination template restriction for ranked-beatmap submission."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from app.database.rules.base import BeatmapRestrictionBase
from app.database.rules.exceptions import RuleViolationError

COMBINATION_TEMPLATES: dict[str, dict[str, Any]] = {
    "any": {
        "operator": "and",
        "rules": [],
    },
}


if TYPE_CHECKING:
    from app.database.rules.context import ExecutionContext


class CombinationRestriction(BeatmapRestrictionBase):
    """Validate the beatmapset against a named combination template."""

    type = "beatmap_combination"

    @override
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
