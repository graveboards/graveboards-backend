import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.database.rules.engine.evaluator import (
    RuleNode,
    AtomicRuleNode,
    CompositeRuleNode,
    AndNode,
    OrNode,
    NotNode,
    CompositeEvaluator,
    MAX_COMPOSITE_DEPTH,
    build_rule_node,
)
from app.database.rules.context import ExecutionContext
from app.database.rules.exceptions import RuleViolationError
from app.database.rules.registry import RULE_REGISTRY, RULE_TIERS


def _make_context(config=None):
    return ExecutionContext(
        queue_id=1,
        user_id=12345678,
        beatmapset=MagicMock(),
        beatmaps=[],
        config=config or {},
    )


class TestAndNode:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_all_pass(self):
        call_log = []

        class AlwaysPass(RuleNode):
            async def evaluate(self, context, depth=0):
                call_log.append("pass")
                return True

        node = AndNode([AlwaysPass("dummy", {}), AlwaysPass("dummy", {})])
        context = _make_context()
        result = await node.evaluate(context)
        assert result is True
        assert call_log == ["pass", "pass"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_first_fails_short_circuits(self):
        call_log = []

        class FailingNode(RuleNode):
            async def evaluate(self, context, depth=0):
                call_log.append("failing")
                return False

        class PassingNode(RuleNode):
            async def evaluate(self, context, depth=0):
                call_log.append("passing")
                return True

        node = AndNode([FailingNode("dummy", {}), PassingNode("dummy", {})])
        context = _make_context()
        result = await node.evaluate(context)

        assert result is False
        assert call_log == ["failing"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_second_fails(self):
        class AlwaysPass(RuleNode):
            async def evaluate(self, context, depth=0):
                return True

        class AlwaysFail(RuleNode):
            async def evaluate(self, context, depth=0):
                return False

        node = AndNode([AlwaysPass("dummy", {}), AlwaysFail("dummy", {})])
        context = _make_context()
        result = await node.evaluate(context)
        assert result is False


class TestOrNode:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_first_pass_short_circuits(self):
        call_log = []

        class AlwaysPass(RuleNode):
            async def evaluate(self, context, depth=0):
                call_log.append("pass")
                return True

        class AlwaysFail(RuleNode):
            async def evaluate(self, context, depth=0):
                call_log.append("fail")
                return False

        node = OrNode([AlwaysPass("dummy", {}), AlwaysFail("dummy", {})])
        context = _make_context()
        result = await node.evaluate(context)

        assert result is True
        assert call_log == ["pass"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_all_fail(self):
        class AlwaysFail(RuleNode):
            async def evaluate(self, context, depth=0):
                return False

        node = OrNode([AlwaysFail("dummy", {}), AlwaysFail("dummy", {})])
        context = _make_context()
        result = await node.evaluate(context)
        assert result is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_second_passes(self):
        class AlwaysFail(RuleNode):
            async def evaluate(self, context, depth=0):
                return False

        class AlwaysPass(RuleNode):
            async def evaluate(self, context, depth=0):
                return True

        node = OrNode([AlwaysFail("dummy", {}), AlwaysPass("dummy", {})])
        context = _make_context()
        result = await node.evaluate(context)
        assert result is True


class TestNotNode:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_negates_true(self):
        class AlwaysPass(RuleNode):
            async def evaluate(self, context, depth=0):
                return True

        node = NotNode(AlwaysPass("dummy", {}))
        context = _make_context()
        result = await node.evaluate(context)
        assert result is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_negates_false(self):
        class AlwaysFail(RuleNode):
            async def evaluate(self, context, depth=0):
                return False

        node = NotNode(AlwaysFail("dummy", {}))
        context = _make_context()
        result = await node.evaluate(context)
        assert result is True


class TestDepthLimit:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_exceeds_max_depth(self):
        inner = AndNode([AtomicRuleNode("beatmap_duration", {"max_seconds": 180})])
        node = AndNode([inner])
        beatmaps = [MagicMock(total_length=150, version="Normal")]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(),
            beatmaps=beatmaps,
            config={},
        )

        with pytest.raises(RuleViolationError) as exc_info:
            await node.evaluate(context, depth=MAX_COMPOSITE_DEPTH)

        assert "depth exceeds maximum" in str(exc_info.value.detail)


class TestBuildRuleNode:
    @pytest.mark.unit
    def test_build_atomic_rule(self):
        rule_data = {"type": "beatmap_duration", "config": {"max_seconds": 180}}
        node = build_rule_node(rule_data)
        assert isinstance(node, AtomicRuleNode)
        assert node.rule_type == "beatmap_duration"
        assert node.config == {"max_seconds": 180}

    @pytest.mark.unit
    def test_build_and_composite(self):
        rule_data = {
            "type": "composite",
            "config": {
                "operator": "and",
                "rules": [
                    {"type": "beatmap_duration", "config": {"max_seconds": 180}},
                    {"type": "beatmap_star_rating", "config": {"max": 6.0}},
                ],
            },
        }
        node = build_rule_node(rule_data)
        assert isinstance(node, AndNode)
        assert len(node.rules) == 2
        assert isinstance(node.rules[0], AtomicRuleNode)
        assert isinstance(node.rules[1], AtomicRuleNode)

    @pytest.mark.unit
    def test_build_or_composite(self):
        rule_data = {
            "type": "composite",
            "config": {
                "operator": "or",
                "rules": [
                    {"type": "beatmap_genre", "config": {"genre_ids": [2]}},
                    {"type": "beatmap_genre", "config": {"genre_ids": [3]}},
                ],
            },
        }
        node = build_rule_node(rule_data)
        assert isinstance(node, OrNode)

    @pytest.mark.unit
    def test_build_not_composite(self):
        rule_data = {
            "type": "composite",
            "config": {
                "operator": "not",
                "rules": [
                    {"type": "beatmap_video", "config": {"allowed": True}},
                ],
            },
        }
        node = build_rule_node(rule_data)
        assert isinstance(node, NotNode)

    @pytest.mark.unit
    def test_build_nested_composite(self):
        rule_data = {
            "type": "composite",
            "config": {
                "operator": "and",
                "rules": [
                    {
                        "type": "composite",
                        "config": {
                            "operator": "or",
                            "rules": [
                                {"type": "beatmap_genre", "config": {"genre_ids": [2]}},
                                {"type": "beatmap_genre", "config": {"genre_ids": [3]}},
                            ],
                        },
                    },
                    {"type": "beatmap_duration", "config": {"max_seconds": 180}},
                ],
            },
        }
        node = build_rule_node(rule_data)
        assert isinstance(node, AndNode)
        assert isinstance(node.rules[0], OrNode)

    @pytest.mark.unit
    def test_build_not_with_multiple_rules_raises(self):
        rule_data = {
            "type": "composite",
            "config": {
                "operator": "not",
                "rules": [
                    {"type": "beatmap_video", "config": {"allowed": True}},
                    {"type": "beatmap_storyboard", "config": {"allowed": True}},
                ],
            },
        }

        with pytest.raises(RuleViolationError):
            build_rule_node(rule_data)

    @pytest.mark.unit
    def test_build_unknown_operator_raises(self):
        rule_data = {
            "type": "composite",
            "config": {
                "operator": "xor",
                "rules": [
                    {"type": "beatmap_video", "config": {"allowed": True}},
                ],
            },
        }

        with pytest.raises(RuleViolationError):
            build_rule_node(rule_data)


class TestCompositeEvaluator:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_evaluate_delegates_to_node(self):
        class AlwaysTrue(RuleNode):
            async def evaluate(self, context, depth=0):
                return True

        node = AlwaysTrue("dummy", {})
        context = _make_context()
        result = await CompositeEvaluator.evaluate(node, context)
        assert result is True


class TestAtomicRuleNodeWithValidator:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_validator_passes(self):
        node = AtomicRuleNode("beatmap_duration", {"max_seconds": 180, "logic": "max"})
        beatmaps = [MagicMock(total_length=150, version="Normal")]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(),
            beatmaps=beatmaps,
            config={},
        )
        result = await node.evaluate(context)
        assert result is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_fails_when_validator_raises(self):
        node = AtomicRuleNode("beatmap_duration", {"max_seconds": 100, "logic": "max"})
        beatmaps = [MagicMock(total_length=150, version="Normal")]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(),
            beatmaps=beatmaps,
            config={},
        )

        result = await node.evaluate(context)
        assert result is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_restores_config_after_evaluation(self):
        class AlwaysPass(RuleNode):
            async def evaluate(self, context, depth=0):
                return True

        node = AlwaysPass("dummy", {})
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(),
            beatmaps=[],
            config={"original": "value"},
        )
        await node.evaluate(context)
        assert context.config == {"original": "value"}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_returns_false_for_unknown_type(self):
        node = AtomicRuleNode("nonexistent_type_xyz", {})
        context = _make_context()
        result = await node.evaluate(context)
        assert result is False
