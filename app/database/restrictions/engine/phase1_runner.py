from __future__ import annotations

import logging
from typing import Any

from app.database.models import QueueRestriction
from app.database.restrictions.engine.evaluator import build_rule_node, RuleNode
from app.database.restrictions.exceptions import RestrictionViolationError

logger = logging.getLogger(__name__)


class Phase1Runner:
    async def run(
        self,
        restrictions: list[QueueRestriction],
        context: Any,
    ) -> None:
        for restriction in restrictions:
            if not restriction.is_active:
                continue

            if not self._check_version(restriction):
                continue

            tier = self._get_tier(restriction.restriction_type)
            if tier not in (1, 2):
                continue

            rule_node = self._build_node(restriction)
            try:
                passed = await rule_node.evaluate(context)
                if not passed:
                    raise RestrictionViolationError(
                        restriction.restriction_type,
                        f"Rule '{restriction.restriction_type}' rejected the request",
                    )
            except RestrictionViolationError:
                raise
            except Exception as e:
                logger.warning(
                    "Phase 1 validator '%s' failed with unexpected error: %s",
                    restriction.restriction_type,
                    e,
                )
                raise RestrictionViolationError(
                    restriction.restriction_type,
                    f"Validation error: {e}",
                )

    def _get_tier(self, restriction_type: str) -> int:
        from app.database.restrictions.registry import get_validator_tier

        tier = get_validator_tier(restriction_type)
        if tier is not None:
            return tier
        if restriction_type == "composite":
            return 2
        return 2

    def _check_version(self, restriction: QueueRestriction) -> bool:
        from app.database.restrictions.registry import get_validator

        validator_cls = get_validator(restriction.restriction_type)
        if validator_cls is None:
            return True
        return restriction.version in validator_cls.supported_versions

    def _build_node(self, restriction: QueueRestriction) -> RuleNode:
        rule_data = {
            "type": restriction.restriction_type,
            "config": restriction.config or {},
        }
        return build_rule_node(rule_data)
