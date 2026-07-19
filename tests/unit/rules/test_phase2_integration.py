import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.database.rules.engine.phase2_runner import Phase2Runner
from app.database.rules.context import ExecutionContext
from app.database.rules.exceptions import RuleViolationError, RetryableValidationError


def _make_mock_rule(type, config, is_active=True):
    r = MagicMock()
    r.type = type
    r.config = config
    r.is_active = is_active
    r.version = "1.0"
    return r


class TestPhase2Runner:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_skips_inactive(self):
        runner = Phase2Runner()
        rule = _make_mock_rule(
            "never_ranked",
            {"ruleset": "osu"},
            is_active=False,
        )
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(),
            osu_client=AsyncMock(),
        )

        rejected = await runner.run([rule], context)
        assert rejected == []

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_collects_rejected_rules(self):
        runner = Phase2Runner()
        rules = [
            _make_mock_rule("never_ranked", {"ruleset": "osu"}),
        ]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(),
            osu_client=AsyncMock(),
        )

        async def mock_evaluate(self, context, depth=0):
            # A genuine policy violation is signalled via context.last_violation,
            # mirroring what the real evaluator records.
            context.last_violation = RuleViolationError("never_ranked", "already ranked")
            return False

        with patch(
            "app.database.rules.engine.evaluator.AtomicRuleNode.evaluate",
            new=mock_evaluate,
        ):
            rejected = await runner.run(rules, context)

        assert "never_ranked" in rejected

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unexpected_exception_is_retryable(self):
        # An unexpected/infra error is neither an accept nor a policy rejection -
        # it raises RetryableValidationError so the job is retried and not marked
        # completed.
        runner = Phase2Runner()
        rules = [
            _make_mock_rule("never_ranked", {"ruleset": "osu"}),
        ]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(),
            osu_client=AsyncMock(),
        )

        async def failing_eval(self, context, depth=0):
            raise ValueError("Unexpected error")

        with patch(
            "app.database.rules.engine.evaluator.AtomicRuleNode.evaluate",
            new=failing_eval,
        ):
            with pytest.raises(RetryableValidationError):
                await runner.run(rules, context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_skips_non_tier3(self):
        runner = Phase2Runner()
        rules = [
            _make_mock_rule("rate_limit", {"max_requests": 5, "period": "day"}),
            _make_mock_rule("beatmap_duration", {"max_seconds": 180, "logic": "max"}),
        ]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(),
        )

        rejected = await runner.run(rules, context)
        assert rejected == []


class TestPhase2RunnerWithComposite:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_composite_rule_in_phase2(self):
        runner = Phase2Runner()
        rules = [
            _make_mock_rule(
                "composite",
                {
                    "operator": "and",
                    "rules": [
                        {"type": "never_ranked", "config": {"ruleset": "osu"}},
                    ],
                },
            ),
        ]
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            beatmapset=MagicMock(),
            osu_client=AsyncMock(),
            db=AsyncMock(),
            redis=AsyncMock(),
        )

        async def mock_evaluate(self, context, depth=0):
            return True

        with patch(
            "app.database.rules.engine.evaluator.AtomicRuleNode.evaluate",
            new=mock_evaluate,
        ):
            rejected = await runner.run(rules, context)

        assert rejected == []
