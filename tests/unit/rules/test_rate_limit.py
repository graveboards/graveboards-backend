from datetime import UTC
from unittest.mock import AsyncMock

import pytest
from connexion.exceptions import Forbidden

from app.database.rules.context import ExecutionContext
from app.database.rules.registry import (
    RULE_REGISTRY,
    RULE_TIERS,
    get_supported_versions,
    get_validator,
    get_validator_tier,
)
from app.database.rules.validators.rate_limit import (
    RateLimitRestriction,
    _period_duration_seconds,
    _truncate_to_period,
)


def _make_context(queue_id: int = 1, user_id: int = 12345678, config: dict | None = None) -> ExecutionContext:
    return ExecutionContext(
        queue_id=queue_id,
        user_id=user_id,
        db=AsyncMock(),
        redis=AsyncMock(),
        config=config or {},
    )


class TestTruncateToPeriod:
    @pytest.mark.unit
    def test_truncate_to_day(self) -> None:
        from datetime import datetime

        dt = datetime(2024, 6, 15, 14, 30, 45, 123456, tzinfo=UTC)
        result = _truncate_to_period(dt, "day")
        expected = datetime(2024, 6, 15, 0, 0, 0, tzinfo=UTC).timestamp()
        assert result == int(expected)

    @pytest.mark.unit
    def test_truncate_to_week(self) -> None:
        from datetime import datetime

        dt = datetime(2024, 6, 15, 14, 30, 0, tzinfo=UTC)
        result = _truncate_to_period(dt, "week")
        expected = datetime(2024, 6, 10, 0, 0, 0, tzinfo=UTC).timestamp()
        assert result == int(expected)

    @pytest.mark.unit
    def test_truncate_to_month(self) -> None:
        from datetime import datetime

        dt = datetime(2024, 6, 15, 14, 30, 0, tzinfo=UTC)
        result = _truncate_to_period(dt, "month")
        expected = datetime(2024, 6, 1, 0, 0, 0, tzinfo=UTC).timestamp()
        assert result == int(expected)

    @pytest.mark.unit
    def test_truncate_to_year(self) -> None:
        from datetime import datetime

        dt = datetime(2024, 6, 15, 14, 30, 0, tzinfo=UTC)
        result = _truncate_to_period(dt, "year")
        expected = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC).timestamp()
        assert result == int(expected)

    @pytest.mark.unit
    def test_truncate_to_custom_seconds(self) -> None:
        from datetime import datetime

        dt = datetime(2024, 6, 15, 14, 30, 45, tzinfo=UTC)
        result = _truncate_to_period(dt, "3600")
        expected = 1718460000
        assert result == expected

    @pytest.mark.unit
    def test_truncate_to_invalid_period_raises(self) -> None:
        from datetime import datetime

        dt = datetime(2024, 6, 15, 14, 30, 0, tzinfo=UTC)
        with pytest.raises(ValueError, match="Invalid period"):
            _truncate_to_period(dt, "invalid")


class TestPeriodDurationSeconds:
    @pytest.mark.unit
    def test_day(self) -> None:
        assert _period_duration_seconds("day") == 86400

    @pytest.mark.unit
    def test_week(self) -> None:
        assert _period_duration_seconds("week") == 604800

    @pytest.mark.unit
    def test_month(self) -> None:
        assert _period_duration_seconds("month") == 2592000

    @pytest.mark.unit
    def test_year(self) -> None:
        assert _period_duration_seconds("year") == 31536000

    @pytest.mark.unit
    def test_custom_seconds(self) -> None:
        assert _period_duration_seconds("3600") == 3600


class TestRateLimitRestriction:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_check_passes_under_limit_without_mutating(self) -> None:
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="0")

        validator = RateLimitRestriction()
        config = {"max_requests": 2, "period": "week", "scope": "user"}
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            db=mock_db,
            redis=mock_redis,
            config=config,
        )

        await validator.check(context)

        mock_redis.get.assert_called_once()
        mock_redis.incr.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_check_raises_when_at_limit(self) -> None:
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="2")

        validator = RateLimitRestriction()
        config = {"max_requests": 2, "period": "week", "scope": "user"}
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            db=mock_db,
            redis=mock_redis,
            config=config,
        )

        with pytest.raises(Forbidden) as exc_info:
            await validator.check(context)

        assert "rate limit" in str(exc_info.value.detail).lower()
        mock_redis.incr.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_check_skips_non_target_user(self) -> None:
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        validator = RateLimitRestriction()
        config = {
            "max_requests": 1,
            "period": "week",
            "scope": "user",
            "target": [99999999],
        }
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            db=mock_db,
            redis=mock_redis,
            config=config,
        )

        await validator.check(context)

        mock_redis.get.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_check_skips_non_user_scope(self) -> None:
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        validator = RateLimitRestriction()
        config = {"max_requests": 1, "period": "week", "scope": "beatmapset_type"}
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            db=mock_db,
            redis=mock_redis,
            config=config,
        )

        await validator.check(context)

        mock_redis.get.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reserve_under_limit_consumes_and_returns_token(self) -> None:
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock(return_value=True)

        validator = RateLimitRestriction()
        config = {"max_requests": 2, "period": "week", "scope": "user"}
        context = ExecutionContext(queue_id=1, user_id=12345678, db=mock_db, redis=mock_redis)

        token = await validator.reserve(context, config)

        assert token is not None
        mock_redis.incr.assert_called_once()
        mock_redis.expire.assert_called_once()
        mock_redis.decr.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reserve_over_limit_rejects_without_consuming(self) -> None:
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=3)

        validator = RateLimitRestriction()
        config = {"max_requests": 2, "period": "week", "scope": "user"}
        context = ExecutionContext(queue_id=1, user_id=12345678, db=mock_db, redis=mock_redis)

        with pytest.raises(Forbidden):
            await validator.reserve(context, config)

        # The rejected request must not consume quota.
        mock_redis.decr.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reserve_skips_non_user_scope(self) -> None:
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        validator = RateLimitRestriction()
        config = {"max_requests": 1, "period": "week", "scope": "beatmapset_type"}
        context = ExecutionContext(queue_id=1, user_id=12345678, db=mock_db, redis=mock_redis)

        token = await validator.reserve(context, config)

        assert token is None
        mock_redis.incr.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_rollback_decrements(self) -> None:
        mock_redis = AsyncMock()
        validator = RateLimitRestriction()
        context = ExecutionContext(queue_id=1, user_id=12345678, db=AsyncMock(), redis=mock_redis)

        await validator.rollback(context, "some-key")

        mock_redis.decr.assert_called_once_with("some-key")

    @pytest.mark.unit
    def test_config_schema_is_set(self) -> None:
        from app.database.schemas.rule import RateLimitConfig

        assert RateLimitRestriction.config_schema is RateLimitConfig

    @pytest.mark.unit
    def test_supported_versions(self) -> None:
        assert RateLimitRestriction.type == "rate_limit"
        assert "1.0" in RateLimitRestriction.supported_versions


class TestRegistry:
    @pytest.mark.unit
    def test_rate_limit_registered(self) -> None:
        validator_cls = get_validator("rate_limit")
        assert validator_cls is not None
        assert validator_cls.type == "rate_limit"

    @pytest.mark.unit
    def test_cooldown_registered(self) -> None:
        from app.database.rules.validators.cooldown import CooldownRestriction

        validator_cls = get_validator("cooldown")
        assert validator_cls is not None
        assert validator_cls is CooldownRestriction

    @pytest.mark.unit
    def test_blacklist_registered(self) -> None:
        from app.database.rules.validators.blacklist import BlacklistRestriction

        validator_cls = get_validator("blacklist")
        assert validator_cls is not None
        assert validator_cls is BlacklistRestriction

    @pytest.mark.unit
    def test_unknown_type_returns_none(self) -> None:
        assert get_validator("nonexistent_type") is None

    @pytest.mark.unit
    def test_all_types_in_registry(self) -> None:
        assert "rate_limit" in RULE_REGISTRY
        assert "cooldown" in RULE_REGISTRY
        assert "blacklist" in RULE_REGISTRY

    @pytest.mark.unit
    def test_tier_assignment(self) -> None:
        assert RULE_TIERS.get("rate_limit") == 1
        assert RULE_TIERS.get("cooldown") == 1
        assert RULE_TIERS.get("blacklist") == 1

    @pytest.mark.unit
    def test_get_validators_for_tier(self) -> None:
        from app.database.rules.registry import get_validators_for_tier

        tier1 = get_validators_for_tier(1)
        assert "rate_limit" in tier1
        assert "cooldown" in tier1
        assert "blacklist" in tier1

    @pytest.mark.unit
    def test_get_validator_tier(self) -> None:
        assert get_validator_tier("rate_limit") == 1
        assert get_validator_tier("cooldown") == 1
        assert get_validator_tier("blacklist") == 1
        assert get_validator_tier("nonexistent") is None

    @pytest.mark.unit
    def test_get_supported_versions(self) -> None:
        versions = get_supported_versions("rate_limit")
        assert versions is not None
        assert "1.0" in versions

    @pytest.mark.unit
    def test_get_supported_versions_unknown_type(self) -> None:
        assert get_supported_versions("nonexistent") is None
