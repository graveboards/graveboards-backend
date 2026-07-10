import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.database.rules.engine.evaluator import build_rule_node, AndNode, OrNode, AtomicRuleNode
from app.database.rules.engine.phase1_runner import Phase1Runner
from app.database.rules.context import ExecutionContext
from app.database.rules.exceptions import RuleViolationError


def _make_mock_rule(type, config, is_active=True):
    r = MagicMock()
    r.type = type
    r.config = config
    r.is_active = is_active
    r.version = "1.0"
    return r


class TestPhase1Runner:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_runs_tier1_and_tier2(self):
        runner = Phase1Runner()
        rules = [
            _make_mock_rule("beatmap_duration", {"max_seconds": 180, "logic": "max"}),
        ]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(),
            beatmaps=[MagicMock(total_length=150, version="Normal")],
            config={},
            db=AsyncMock(),
            redis=AsyncMock(),
        )
        await runner.run(rules, context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_skips_inactive(self):
        runner = Phase1Runner()
        rule = _make_mock_rule(
            "beatmap_duration",
            {"max_seconds": 100, "logic": "max"},
            is_active=False,
        )
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(),
            beatmaps=[MagicMock(total_length=150, version="Normal")],
            config={},
        )
        await runner.run([rule], context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_on_violation(self):
        runner = Phase1Runner()
        rules = [
            _make_mock_rule("beatmap_duration", {"max_seconds": 100, "logic": "max"}),
        ]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(),
            beatmaps=[MagicMock(total_length=150, version="Normal")],
            config={},
        )

        with pytest.raises(RuleViolationError):
            await runner.run(rules, context)


class TestVersionChecking:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_skips_unsupported_version(self):
        runner = Phase1Runner()
        rule = _make_mock_rule(
            "beatmap_duration",
            {"max_seconds": 100, "logic": "max"},
            is_active=True,
        )
        rule.version = "99.0"

        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(),
            beatmaps=[MagicMock(total_length=150, version="Normal")],
            config={},
            db=AsyncMock(),
            redis=AsyncMock(),
        )

        await runner.run([rule], context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_runs_supported_version(self):
        runner = Phase1Runner()
        rule = _make_mock_rule(
            "beatmap_duration",
            {"max_seconds": 200, "logic": "max"},
            is_active=True,
        )
        rule.version = "1.0"

        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(),
            beatmaps=[MagicMock(total_length=150, version="Normal")],
            config={},
            db=AsyncMock(),
            redis=AsyncMock(),
        )

        await runner.run([rule], context)


class TestEndToEndComposite:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_and_composite_passes(self):
        rule_data = {
            "type": "composite",
            "config": {
                "operator": "and",
                "rules": [
                    {"type": "beatmap_duration", "config": {"max_seconds": 200, "logic": "max"}},
                    {"type": "beatmap_star_rating", "config": {"max": 7.0, "logic": "any"}},
                ],
            },
        }
        node = build_rule_node(rule_data)
        beatmaps = [MagicMock(total_length=150, difficulty_rating=5.0, version="Normal")]
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
    async def test_or_composite_passes_on_either(self):
        rule_data = {
            "type": "composite",
            "config": {
                "operator": "or",
                "rules": [
                    {"type": "beatmap_duration", "config": {"max_seconds": 100, "logic": "max"}},
                    {"type": "beatmap_duration", "config": {"max_seconds": 200, "logic": "max"}},
                ],
            },
        }
        node = build_rule_node(rule_data)
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
    async def test_nested_composite(self):
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
                                {"type": "beatmap_duration", "config": {"max_seconds": 100, "logic": "max"}},
                                {"type": "beatmap_duration", "config": {"max_seconds": 200, "logic": "max"}},
                            ],
                        },
                    },
                    {"type": "beatmap_star_rating", "config": {"max": 7.0, "logic": "any"}},
                ],
            },
        }
        node = build_rule_node(rule_data)
        beatmaps = [MagicMock(total_length=150, difficulty_rating=5.0, version="Normal")]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(),
            beatmaps=beatmaps,
            config={},
        )
        result = await node.evaluate(context)
        assert result is True
