"""Rule node model and the composite evaluator entry point."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

from connexion.exceptions import Forbidden

from app.database.rules.exceptions import RuleViolationError
from app.database.rules.registry import get_validator

if TYPE_CHECKING:
    from app.database.rules.context import ExecutionContext

logger = logging.getLogger(__name__)

MAX_COMPOSITE_DEPTH = 10


class RuleNode:
    """Base class for a node in the rule evaluation tree."""

    def __init__(self, rule_type: str, config: dict[str, Any]):
        self.rule_type = rule_type
        self.config = config

    async def evaluate(self, context: ExecutionContext, depth: int = 0) -> bool:
        """Evaluate this node against the context (implemented by subclasses)."""
        raise NotImplementedError


class AtomicRuleNode(RuleNode):
    """Evaluates a single registered rule restriction."""

    def __init__(self, rule_type: str, config: dict[str, Any]):
        super().__init__(rule_type, config)
        self._validator_cls = get_validator(rule_type)

    async def evaluate(self, context: ExecutionContext, _depth: int = 0) -> bool:
        """Evaluate this node's rule against the context, catching violations."""
        if self._validator_cls is None:
            context.last_violation = RuleViolationError(
                self.rule_type, f"Unknown rule type '{self.rule_type}'"
            )
            return False

        original_config = context.config
        context.config = self.config

        try:
            validator = self._validator_cls()
            await validator.check(context)
            return True
        except RuleViolationError as e:
            context.last_violation = e
            return False
        except Forbidden:
            raise
        except Exception:
            logger.exception("Unexpected error evaluating rule '%s'", self.rule_type)
            return False
        finally:
            context.config = original_config


class CompositeRuleNode(RuleNode):
    """Base class for a node combining child nodes with a boolean operator."""

    def __init__(self, operator: str, rules: list[RuleNode]):
        super().__init__("composite", {"operator": operator, "rules": rules})
        self.operator = operator
        self.rules = rules


class AndNode(CompositeRuleNode):
    """A composite node that passes only when every child passes."""

    def __init__(self, rules: list[RuleNode]):
        super().__init__("and", rules)

    async def evaluate(self, context: ExecutionContext, depth: int = 0) -> bool:
        """Evaluate every child, passing only when all pass."""
        if depth > MAX_COMPOSITE_DEPTH:
            raise RuleViolationError(
                "composite",
                "Rule nesting depth exceeds maximum (10)",
            )
        for rule in self.rules:
            if not await rule.evaluate(context, depth + 1):
                return False
        return True


class OrNode(CompositeRuleNode):
    """A composite node that passes when any child passes."""

    def __init__(self, rules: list[RuleNode]):
        super().__init__("or", rules)

    async def evaluate(self, context: ExecutionContext, depth: int = 0) -> bool:
        """Evaluate every child, passing when any child passes."""
        if depth > MAX_COMPOSITE_DEPTH:
            raise RuleViolationError(
                "composite",
                "Rule nesting depth exceeds maximum (10)",
            )
        for rule in self.rules:
            if await rule.evaluate(context, depth + 1):
                return True
        return False


class NotNode(CompositeRuleNode):
    """A composite node that negates its single child."""

    def __init__(self, rule: RuleNode):
        super().__init__("not", [rule])

    async def evaluate(self, context: ExecutionContext, depth: int = 0) -> bool:
        """Evaluate the single child, inverting its result."""
        if depth > MAX_COMPOSITE_DEPTH:
            raise RuleViolationError(
                "composite",
                "Rule nesting depth exceeds maximum (10)",
            )
        if len(self.rules) != 1:
            raise RuleViolationError(
                "composite",
                "NOT operator requires exactly one rule",
            )
        return not await self.rules[0].evaluate(context, depth + 1)


class CompositeEvaluator:
    """Entry point that evaluates a root rule node against a context."""

    @staticmethod
    async def evaluate(node: RuleNode, context: ExecutionContext) -> bool:
        """Evaluate a root node against the context."""
        return await node.evaluate(context)


_RULE_TYPE_TO_NODE_CLASS: dict[str, Any] = {
    "and": AndNode,
    "or": OrNode,
    "not": NotNode,
}


def build_rule_node(
    rule_data: dict[str, Any],
) -> RuleNode:
    """Build a rule node tree from a raw rule dict.

    Recurses into ``composite`` rules using their configured operator, producing an
    ``AtomicRuleNode`` for everything else.
    """
    rule_type = rule_data.get("type", "")
    config = rule_data.get("config", {})

    if rule_type == "composite":
        operator = config.get("operator", "and")
        child_rules = config.get("rules", [])

        if operator == "not":
            if len(child_rules) != 1:
                raise RuleViolationError(
                    "composite",
                    "NOT operator requires exactly one child rule",
                )
            child_node = build_rule_node(child_rules[0])
            return NotNode(child_node)

        node_cls = _RULE_TYPE_TO_NODE_CLASS.get(operator)
        if node_cls is None:
            raise RuleViolationError(
                "composite",
                f"Unknown composite operator: {operator}",
            )

        children = [build_rule_node(r) for r in child_rules]
        return cast("RuleNode", node_cls(children))

    return AtomicRuleNode(rule_type, config)
