from __future__ import annotations

import asyncio
import logging
from enum import Enum
from typing import Any

from connexion.exceptions import Forbidden

from app.database.models import QueueRule
from app.database.rules.engine.evaluator import build_rule_node, RuleNode
from app.database.rules.exceptions import RuleViolationError, RetryableValidationError
from app.database.rules.registry import effective_rule_tier

logger = logging.getLogger(__name__)

TIER3_TIMEOUT = 30


class Tier3Outcome(Enum):
    """Explicit terminal/non-terminal outcomes for a Tier-3 validation."""

    PASS = "pass"
    VIOLATION = "violation"
    RETRYABLE = "retryable"


class Phase2Runner:
    async def run(
        self,
        rules: list[QueueRule],
        context: Any,
    ) -> list[str]:
        """Run Tier-3 validators and return the rule types that rejected the request.

        Outcomes are explicit. A genuine policy VIOLATION rejects the request;
        a RETRYABLE infrastructure/unexpected error does NOT silently accept or
        reject - it raises RetryableValidationError so the caller can avoid
        marking the work completed and retry it instead. Rejections take
        precedence over retryable errors.
        """
        tasks = []

        for rule in rules:
            if not rule.is_active:
                continue

            if not self._check_version(rule):
                continue

            tier = self._get_tier(rule)
            if tier != 3:
                continue

            tasks.append(self._validate_one(rule, context))

        if not tasks:
            return []

        outcomes = await asyncio.gather(*tasks)

        rejected = [rt for rt, outcome in outcomes if outcome is Tier3Outcome.VIOLATION]
        retryable = [rt for rt, outcome in outcomes if outcome is Tier3Outcome.RETRYABLE]

        if rejected:
            return rejected

        if retryable:
            raise RetryableValidationError(
                retryable,
                f"Tier-3 validation did not reach a terminal outcome for: {retryable}",
            )

        return []

    async def _validate_one(
        self,
        rule: QueueRule,
        context: Any,
    ) -> tuple[str, Tier3Outcome]:
        try:
            async with asyncio.timeout(TIER3_TIMEOUT):
                context.last_violation = None
                rule_node = self._build_node(rule)
                passed = await rule_node.evaluate(context)

            if passed:
                return rule.type, Tier3Outcome.PASS

            # Only a captured RuleViolationError is a genuine policy rejection.
            # A bare False with no violation means the evaluator swallowed an
            # unexpected error - treat that as retryable, not a rejection, so
            # infra/programming faults do not masquerade as policy.
            if isinstance(context.last_violation, RuleViolationError):
                return rule.type, Tier3Outcome.VIOLATION
            logger.warning(
                "Phase 2 validator '%s' returned no pass and no violation; "
                "treating as retryable",
                rule.type,
            )
            return rule.type, Tier3Outcome.RETRYABLE
        except RuleViolationError:
            return rule.type, Tier3Outcome.VIOLATION
        except asyncio.TimeoutError:
            logger.warning(
                "Phase 2 validator '%s' timed out after %ds",
                rule.type,
                TIER3_TIMEOUT,
            )
            return rule.type, Tier3Outcome.RETRYABLE
        except Forbidden:
            # A Tier-1 child inside a composite raised Forbidden; surface as a
            # rejection rather than a retry.
            return rule.type, Tier3Outcome.VIOLATION
        except Exception as e:
            logger.warning(
                "Phase 2 validator '%s' failed with unexpected error: %s",
                rule.type,
                e,
            )
            return rule.type, Tier3Outcome.RETRYABLE

    def _get_tier(self, rule: QueueRule) -> int:
        return effective_rule_tier(rule.type, rule.config or {})

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
