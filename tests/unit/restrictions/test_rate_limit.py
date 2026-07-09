import pytest
from unittest.mock import AsyncMock, MagicMock

from connexion.exceptions import Forbidden

from app.database.restrictions.validators.rate_limit import (
    RateLimitRestriction,
    _truncate_to_period,
    _period_duration_seconds,
)
from app.database.restrictions.registry import (
    get_validator,
    get_validator_tier,
    get_supported_versions,
    RESTRICTION_REGISTRY,
    RESTRICTION_TIERS,
)
from app.database.restrictions.context import ExecutionContext


def _make_context(queue_id: int = 1, user_id: int = 12345678, config: dict | None = None):
    return ExecutionContext(
        queue_id=queue_id,
        user_id=user_id,
        db=AsyncMock(),
        redis=AsyncMock(),
        config=config or {},
    )


class TestTruncateToPeriod:
    @pytest.mark.unit
    def test_truncate_to_day(self):
        from datetime import datetime, timezone, time

        dt = datetime(2024, 6, 15, 14, 30, 45, 123456, tzinfo=timezone.utc)
        result = _truncate_to_period(dt, "day")
        expected = datetime(2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc).timestamp()
        assert result == int(expected)

    @pytest.mark.unit
    def test_truncate_to_week(self):
        from datetime import datetime, timezone

        dt = datetime(2024, 6, 15, 14, 30, 0, tzinfo=timezone.utc)
        result = _truncate_to_period(dt, "week")
        expected = datetime(2024, 6, 10, 0, 0, 0, tzinfo=timezone.utc).timestamp()
        assert result == int(expected)

    @pytest.mark.unit
    def test_truncate_to_month(self):
        from datetime import datetime, timezone

        dt = datetime(2024, 6, 15, 14, 30, 0, tzinfo=timezone.utc)
        result = _truncate_to_period(dt, "month")
        expected = datetime(2024, 6, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp()
        assert result == int(expected)

    @pytest.mark.unit
    def test_truncate_to_year(self):
        from datetime import datetime, timezone

        dt = datetime(2024, 6, 15, 14, 30, 0, tzinfo=timezone.utc)
        result = _truncate_to_period(dt, "year")
        expected = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp()
        assert result == int(expected)

    @pytest.mark.unit
    def test_truncate_to_custom_seconds(self):
        from datetime import datetime, timezone

        dt = datetime(2024, 6, 15, 14, 30, 45, tzinfo=timezone.utc)
        result = _truncate_to_period(dt, "3600")
        expected = 1718460000
        assert result == expected

    @pytest.mark.unit
    def test_truncate_to_invalid_period_raises(self):
        from datetime import datetime, timezone

        dt = datetime(2024, 6, 15, 14, 30, 0, tzinfo=timezone.utc)
        with pytest.raises(ValueError, match="Invalid period"):
            _truncate_to_period(dt, "invalid")


class TestPeriodDurationSeconds:
    @pytest.mark.unit
    def test_day(self):
        assert _period_duration_seconds("day") == 86400

    @pytest.mark.unit
    def test_week(self):
        assert _period_duration_seconds("week") == 604800

    @pytest.mark.unit
    def test_month(self):
        assert _period_duration_seconds("month") == 2592000

    @pytest.mark.unit
    def test_year(self):
        assert _period_duration_seconds("year") == 31536000

    @pytest.mark.unit
    def test_custom_seconds(self):
        assert _period_duration_seconds("3600") == 3600


class TestRateLimitRestriction:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_under_limit(self):
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock(return_value=True)

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

        mock_redis.incr.assert_called_once()
        mock_redis.expire.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_over_limit(self):
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=3)

        validator = RateLimitRestriction()
        config = {"max_requests": 2, "period": "week", "scope": "user"}
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            db=mock_db,
            redis=mock_redis,
            config=config,
        )

        with pytest.raises(Exception) as exc_info:
            await validator.check(context)

        assert "rate limit" in str(exc_info.value.detail).lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_skips_non_target_user(self):
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

        mock_redis.incr.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_skips_non_user_scope(self):
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

        mock_redis.incr.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_forbidden_on_violation(self):
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.incr = AsyncMock(return_value=3)

        validator = RateLimitRestriction()
        config = {"max_requests": 2, "period": "week", "scope": "user"}
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            db=mock_db,
            redis=mock_redis,
            config=config,
        )

        with pytest.raises(Forbidden):
            await validator.check(context)

    @pytest.mark.unit
    def test_config_schema_is_set(self):
        from app.database.schemas.restriction import RateLimitConfig

        assert RateLimitRestriction.config_schema is RateLimitConfig

    @pytest.mark.unit
    def test_supported_versions(self):
        assert RateLimitRestriction.restriction_type == "rate_limit"
        assert "1.0" in RateLimitRestriction.supported_versions


class TestRegistry:
    @pytest.mark.unit
    def test_rate_limit_registered(self):
        validator_cls = get_validator("rate_limit")
        assert validator_cls is not None
        assert validator_cls.restriction_type == "rate_limit"

    @pytest.mark.unit
    def test_cooldown_registered(self):
        from app.database.restrictions.validators.cooldown import CooldownRestriction

        validator_cls = get_validator("cooldown")
        assert validator_cls is not None
        assert validator_cls is CooldownRestriction

    @pytest.mark.unit
    def test_blacklist_registered(self):
        from app.database.restrictions.validators.blacklist import BlacklistRestriction

        validator_cls = get_validator("blacklist")
        assert validator_cls is not None
        assert validator_cls is BlacklistRestriction

    @pytest.mark.unit
    def test_unknown_type_returns_none(self):
        assert get_validator("nonexistent_type") is None

    @pytest.mark.unit
    def test_all_types_in_registry(self):
        assert "rate_limit" in RESTRICTION_REGISTRY
        assert "cooldown" in RESTRICTION_REGISTRY
        assert "blacklist" in RESTRICTION_REGISTRY

    @pytest.mark.unit
    def test_tier_assignment(self):
        assert RESTRICTION_TIERS.get("rate_limit") == 1
        assert RESTRICTION_TIERS.get("cooldown") == 1
        assert RESTRICTION_TIERS.get("blacklist") == 1

    @pytest.mark.unit
    def test_get_validators_for_tier(self):
        from app.database.restrictions.registry import get_validators_for_tier

        tier1 = get_validators_for_tier(1)
        assert "rate_limit" in tier1
        assert "cooldown" in tier1
        assert "blacklist" in tier1

    @pytest.mark.unit
    def test_get_validator_tier(self):
        assert get_validator_tier("rate_limit") == 1
        assert get_validator_tier("cooldown") == 1
        assert get_validator_tier("blacklist") == 1
        assert get_validator_tier("nonexistent") is None

    @pytest.mark.unit
    def test_get_supported_versions(self):
        versions = get_supported_versions("rate_limit")
        assert versions is not None
        assert "1.0" in versions

    @pytest.mark.unit
    def test_get_supported_versions_unknown_type(self):
        assert get_supported_versions("nonexistent") is None
