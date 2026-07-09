import time
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.database.restrictions.engine.phase1_runner import Phase1Runner
from app.database.restrictions.context import ExecutionContext


def _make_mock_restriction(restriction_type, config, is_active=True):
    r = MagicMock()
    r.restriction_type = restriction_type
    r.config = config
    r.is_active = is_active
    r.version = "1.0"
    return r


def _make_mock_context():
    return ExecutionContext(
        queue_id=1,
        user_id=12345678,
        beatmapset=MagicMock(),
        beatmaps=[MagicMock(total_length=150, difficulty_rating=5.0, version="Normal")],
        config={},
        db=AsyncMock(),
        redis=AsyncMock(),
    )


class TestPhase1Benchmark:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_10_rules_under_10ms(self):
        runner = Phase1Runner()
        restrictions = [
            _make_mock_restriction("beatmap_duration", {"max_seconds": 200, "logic": "max"}),
            _make_mock_restriction("beatmap_star_rating", {"max": 7.0, "logic": "any"}),
            _make_mock_restriction("beatmap_duration", {"max_seconds": 200, "logic": "max"}),
            _make_mock_restriction("beatmap_star_rating", {"max": 7.0, "logic": "any"}),
            _make_mock_restriction("beatmap_duration", {"max_seconds": 200, "logic": "max"}),
            _make_mock_restriction("beatmap_star_rating", {"max": 7.0, "logic": "any"}),
            _make_mock_restriction("beatmap_duration", {"max_seconds": 200, "logic": "max"}),
            _make_mock_restriction("beatmap_star_rating", {"max": 7.0, "logic": "any"}),
            _make_mock_restriction("beatmap_duration", {"max_seconds": 200, "logic": "max"}),
            _make_mock_restriction("beatmap_star_rating", {"max": 7.0, "logic": "any"}),
        ]
        context = _make_mock_context()

        start = time.perf_counter()
        await runner.run(restrictions, context)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 10, f"10 rules took {elapsed_ms:.2f}ms, expected < 10ms"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_50_rules_under_500ms(self):
        runner = Phase1Runner()
        restrictions = []
        for i in range(50):
            if i % 2 == 0:
                restrictions.append(
                    _make_mock_restriction(
                        "beatmap_duration",
                        {"max_seconds": 200, "logic": "max"},
                    )
                )
            else:
                restrictions.append(
                    _make_mock_restriction(
                        "beatmap_star_rating",
                        {"max": 7.0, "logic": "any"},
                    )
                )
        context = _make_mock_context()

        start = time.perf_counter()
        await runner.run(restrictions, context)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 500, f"50 rules took {elapsed_ms:.2f}ms, expected < 500ms"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_single_rule_under_5ms(self):
        runner = Phase1Runner()
        restrictions = [
            _make_mock_restriction("beatmap_duration", {"max_seconds": 200, "logic": "max"}),
        ]
        context = _make_mock_context()

        start = time.perf_counter()
        await runner.run(restrictions, context)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 5, f"1 rule took {elapsed_ms:.2f}ms, expected < 5ms"
