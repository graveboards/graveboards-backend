from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.database.models import QueueRestriction
from app.database.restrictions.engine.evaluator import build_rule_node, RuleNode
from app.database.restrictions.exceptions import RestrictionViolationError

logger = logging.getLogger(__name__)

TIER3_TIMEOUT = 30


class Phase2Runner:
    async def run(
        self,
        restrictions: list[QueueRestriction],
        context: Any,
    ) -> list[str]:
        rejected: list[str] = []
        tasks = []

        for restriction in restrictions:
            if not restriction.is_active:
                continue

            tier = self._get_tier(restriction.restriction_type)
            if tier != 3:
                continue

            tasks.append(self._validate_one(restriction, context, rejected))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        return rejected

    async def _validate_one(
        self,
        restriction: QueueRestriction,
        context: Any,
        rejected: list[str],
    ) -> None:
        try:
            async with asyncio.timeout(TIER3_TIMEOUT):
                rule_node = self._build_node(restriction)
                passed = await rule_node.evaluate(context)
                if not passed:
                    rejected.append(restriction.restriction_type)
        except asyncio.TimeoutError:
            logger.warning(
                "Phase 2 validator '%s' timed out after %ds",
                restriction.restriction_type,
                TIER3_TIMEOUT,
            )
        except RestrictionViolationError:
            rejected.append(restriction.restriction_type)
        except Exception as e:
            logger.warning(
                "Phase 2 validator '%s' failed with unexpected error: %s",
                restriction.restriction_type,
                e,
            )

    def _get_tier(self, restriction_type: str) -> int:
        from app.database.restrictions.registry import get_validator_tier

        return get_validator_tier(restriction_type) or 3

    def _build_node(self, restriction: QueueRestriction) -> RuleNode:
        rule_data = {
            "type": restriction.restriction_type,
            "config": restriction.config or {},
        }
        return build_rule_node(rule_data)
