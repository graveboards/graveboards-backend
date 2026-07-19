from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.database.models import QueueRule
from app.database.rules.engine.evaluator import build_rule_node, RuleNode
from app.database.rules.exceptions import RuleViolationError

logger = logging.getLogger(__name__)

TIER3_TIMEOUT = 30


class Phase2Runner:
    async def run(
        self,
        rules: list[QueueRule],
        context: Any,
    ) -> list[str]:
        rejected: list[str] = []
        tasks = []

        for rule in rules:
            if not rule.is_active:
                continue

            if not self._check_version(rule):
                continue

            tier = self._get_tier(rule.type)
            if tier != 3:
                continue

            tasks.append(self._validate_one(rule, context, rejected))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        return rejected

    async def _validate_one(
        self,
        rule: QueueRule,
        context: Any,
        rejected: list[str],
    ) -> None:
        try:
            async with asyncio.timeout(TIER3_TIMEOUT):
                rule_node = self._build_node(rule)
                passed = await rule_node.evaluate(context)
                if not passed:
                    rejected.append(rule.type)
        except asyncio.TimeoutError:
            logger.warning(
                "Phase 2 validator '%s' timed out after %ds",
                rule.type,
                TIER3_TIMEOUT,
            )
        except RuleViolationError:
            rejected.append(rule.type)
        except Exception as e:
            logger.warning(
                "Phase 2 validator '%s' failed with unexpected error: %s",
                rule.type,
                e,
            )

    def _get_tier(self, type: str) -> int:
        from app.database.rules.registry import get_validator_tier

        return get_validator_tier(type) or 3

    def _check_version(self, rule: QueueRule) -> bool:
        from app.database.rules.registry import get_validator

        validator_cls = get_validator(rule.type)
        if validator_cls is None:
            return True
        supported = rule.version in validator_cls.supported_versions
        if not supported:
            logger.error(
                "Skipping active rule id=%s type=%s: unsupported version '%s' "
                "(supported: %s)",
                getattr(rule, "id", "?"),
                rule.type,
                rule.version,
                sorted(validator_cls.supported_versions),
            )
        return supported

    def _build_node(self, rule: QueueRule) -> RuleNode:
        rule_data = {
            "type": rule.type,
            "config": rule.config or {},
        }
        return build_rule_node(rule_data)
