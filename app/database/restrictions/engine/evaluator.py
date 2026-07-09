from __future__ import annotations

from typing import Any

from app.database.restrictions.context import ExecutionContext
from app.database.restrictions.exceptions import RestrictionViolationError
from app.database.restrictions.registry import get_validator, get_validator_tier


MAX_COMPOSITE_DEPTH = 10


class RuleNode:
    def __init__(self, rule_type: str, config: dict[str, Any]):
        self.rule_type = rule_type
        self.config = config

    async def evaluate(
        self, context: ExecutionContext, depth: int = 0
    ) -> bool:
        raise NotImplementedError


class AtomicRuleNode(RuleNode):
    def __init__(self, rule_type: str, config: dict[str, Any]):
        super().__init__(rule_type, config)
        self._validator_cls = get_validator(rule_type)

    async def evaluate(
        self, context: ExecutionContext, depth: int = 0
    ) -> bool:
        if self._validator_cls is None:
            return True

        original_config = context.config
        context.config = self.config

        try:
            validator = self._validator_cls()
            await validator.check(context)
            return True
        except RestrictionViolationError:
            return False
        except Exception:
            return False
        finally:
            context.config = original_config


class CompositeRuleNode(RuleNode):
    def __init__(self, operator: str, rules: list[RuleNode]):
        super().__init__("composite", {"operator": operator, "rules": rules})
        self.operator = operator
        self.rules = rules


class AndNode(CompositeRuleNode):
    def __init__(self, rules: list[RuleNode]):
        super().__init__("and", rules)

    async def evaluate(
        self, context: ExecutionContext, depth: int = 0
    ) -> bool:
        if depth > MAX_COMPOSITE_DEPTH:
            raise RestrictionViolationError(
                "composite",
                "Rule nesting depth exceeds maximum (10)",
            )
        for rule in self.rules:
            if not await rule.evaluate(context, depth + 1):
                return False
        return True


class OrNode(CompositeRuleNode):
    def __init__(self, rules: list[RuleNode]):
        super().__init__("or", rules)

    async def evaluate(
        self, context: ExecutionContext, depth: int = 0
    ) -> bool:
        if depth > MAX_COMPOSITE_DEPTH:
            raise RestrictionViolationError(
                "composite",
                "Rule nesting depth exceeds maximum (10)",
            )
        for rule in self.rules:
            if await rule.evaluate(context, depth + 1):
                return True
        return False


class NotNode(CompositeRuleNode):
    def __init__(self, rule: RuleNode):
        super().__init__("not", [rule])

    async def evaluate(
        self, context: ExecutionContext, depth: int = 0
    ) -> bool:
        if depth > MAX_COMPOSITE_DEPTH:
            raise RestrictionViolationError(
                "composite",
                "Rule nesting depth exceeds maximum (10)",
            )
        if len(self.rules) != 1:
            raise RestrictionViolationError(
                "composite",
                "NOT operator requires exactly one rule",
            )
        return not await self.rules[0].evaluate(context, depth + 1)


class CompositeEvaluator:
    @staticmethod
    async def evaluate(node: RuleNode, context: ExecutionContext) -> bool:
        return await node.evaluate(context)


_RULE_TYPE_TO_NODE_CLASS = {
    "and": AndNode,
    "or": OrNode,
    "not": NotNode,
}


def build_rule_node(
    rule_data: dict[str, Any],
) -> RuleNode:
    rule_type = rule_data.get("type", "")
    config = rule_data.get("config", {})

    if rule_type == "composite":
        operator = config.get("operator", "and")
        child_rules = config.get("rules", [])

        if operator == "not":
            if len(child_rules) != 1:
                raise RestrictionViolationError(
                    "composite",
                    "NOT operator requires exactly one child rule",
                )
            child_node = build_rule_node(child_rules[0])
            return NotNode(child_node)

        node_cls = _RULE_TYPE_TO_NODE_CLASS.get(operator)
        if node_cls is None:
            raise RestrictionViolationError(
                "composite",
                f"Unknown composite operator: {operator}",
            )

        children = [build_rule_node(r) for r in child_rules]
        return node_cls(children)

    return AtomicRuleNode(rule_type, config)
