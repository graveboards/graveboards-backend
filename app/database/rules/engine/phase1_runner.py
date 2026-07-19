from __future__ import annotations

import logging
from typing import Any

from connexion.exceptions import Forbidden

from app.database.models import QueueRule
from app.database.rules.engine.evaluator import build_rule_node, RuleNode
from app.database.rules.engine.stateful import STATEFUL_RULE_TYPES
from app.database.rules.exceptions import RuleViolationError

logger = logging.getLogger(__name__)


class Phase1Runner:
    async def run(
        self,
        rules: list[QueueRule],
        context: Any,
    ) -> None:
        for rule in rules:
            if not rule.is_active:
                continue

            if rule.type in STATEFUL_RULE_TYPES:
                continue

            if not self._check_version(rule):
                continue

            tier = self._get_tier(rule.type)
            if tier not in (1, 2):
                continue

            rule_node = self._build_node(rule)
            context.last_violation = None
            try:
                passed = await rule_node.evaluate(context)
                if not passed:
                    violation = context.last_violation
                    if isinstance(violation, RuleViolationError):
                        raise violation
                    raise RuleViolationError(
                        rule.type,
                        f"Rule '{rule.type}' rejected the request",
                    )
            except RuleViolationError:
                raise
            except Forbidden:
                raise
            except Exception as e:
                logger.warning(
                    "Phase 1 validator '%s' failed with unexpected error: %s",
                    rule.type,
                    e,
                )
                raise RuleViolationError(
                    rule.type,
                    f"Validation error: {e}",
                )

    def _get_tier(self, type: str) -> int:
        from app.database.rules.registry import get_validator_tier

        tier = get_validator_tier(type)
        if tier is not None:
            return tier
        if type == "composite":
            return 2
        return 2

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
