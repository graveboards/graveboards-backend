import pytest
from unittest.mock import AsyncMock, MagicMock

from connexion.exceptions import Forbidden

from app.database.rules.context import ExecutionContext
from app.database.rules.engine.stateful import (
    reserve_stateful_rules,
    rollback_reservations,
    STATEFUL_RULE_TYPES,
    Reservation,
)


def _rule(type_, config, is_active=True, version="1.0"):
    rule = MagicMock()
    rule.type = type_
    rule.config = config
    rule.is_active = is_active
    rule.version = version
    return rule


class TestReserveStatefulRules:
    @pytest.mark.unit
    def test_stateful_types(self):
        assert STATEFUL_RULE_TYPES == frozenset({"rate_limit", "cooldown"})

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reserves_stateful_rules_and_skips_others(self):
        redis = AsyncMock()
        redis.incr = AsyncMock(return_value=1)
        redis.set = AsyncMock(return_value=True)
        context = ExecutionContext(queue_id=1, user_id=42, db=AsyncMock(), redis=redis)

        rules = [
            _rule("rate_limit", {"max_requests": 5, "period": "week", "scope": "user"}),
            _rule("beatmap_duration", {"max_seconds": 100, "logic": "max"}),
            _rule("cooldown", {"cooldown_seconds": 60, "scope": "user"}),
        ]

        reservations = await reserve_stateful_rules(rules, context)

        # Only the two stateful rules are reserved; the beatmap rule is ignored here.
        assert len(reservations) == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_rejection_rolls_back_prior_reservations(self):
        redis = AsyncMock()
        redis.incr = AsyncMock(return_value=1)      # rate_limit reserves successfully
        redis.set = AsyncMock(return_value=None)     # cooldown SET NX fails -> Forbidden
        redis.get = AsyncMock(return_value=None)
        context = ExecutionContext(queue_id=1, user_id=42, db=AsyncMock(), redis=redis)

        rules = [
            _rule("rate_limit", {"max_requests": 5, "period": "week", "scope": "user"}),
            _rule("cooldown", {"cooldown_seconds": 60, "scope": "user"}),
        ]

        with pytest.raises(Forbidden):
            await reserve_stateful_rules(rules, context)

        # The already-made rate-limit reservation must be rolled back (DECR).
        redis.decr.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_skips_inactive_and_unsupported_version(self):
        redis = AsyncMock()
        redis.incr = AsyncMock(return_value=1)
        context = ExecutionContext(queue_id=1, user_id=42, db=AsyncMock(), redis=redis)

        rules = [
            _rule("rate_limit", {"max_requests": 5, "period": "week", "scope": "user"}, is_active=False),
            _rule("cooldown", {"cooldown_seconds": 60, "scope": "user"}, version="99.0"),
        ]

        reservations = await reserve_stateful_rules(rules, context)

        assert reservations == []


class TestRollbackReservations:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_calls_rollback_on_each(self):
        context = ExecutionContext(queue_id=1, user_id=42, db=AsyncMock(), redis=AsyncMock())
        v1 = AsyncMock()
        v2 = AsyncMock()
        reservations = [Reservation(v1, "k1"), Reservation(v2, "k2")]

        await rollback_reservations(reservations, context)

        v1.rollback.assert_awaited_once_with(context, "k1")
        v2.rollback.assert_awaited_once_with(context, "k2")
