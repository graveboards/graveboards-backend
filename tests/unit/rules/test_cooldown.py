import pytest
from unittest.mock import AsyncMock

from connexion.exceptions import Forbidden

from app.database.rules.validators.cooldown import (
    CooldownRestriction,
)
from app.database.rules.context import ExecutionContext
from app.database.rules.exceptions import RuleViolationError


def _make_context(queue_id: int = 1, user_id: int = 12345678, config: dict | None = None):
    return ExecutionContext(
        queue_id=queue_id,
        user_id=user_id,
        db=AsyncMock(),
        redis=AsyncMock(),
        config=config or {},
    )


class TestCooldownRestriction:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_check_passes_on_first_request_without_mutating(self):
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)

        validator = CooldownRestriction()
        config = {"cooldown_seconds": 3600, "scope": "user"}
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            db=mock_db,
            redis=mock_redis,
            config=config,
        )

        await validator.check(context)

        mock_redis.get.assert_called_once()
        mock_redis.set.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_cooldown_active(self):
        from datetime import datetime, timezone, timedelta

        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        now = datetime.now(timezone.utc)
        thirty_minutes_ago = int((now - timedelta(minutes=30)).timestamp())
        mock_redis.get = AsyncMock(return_value=str(thirty_minutes_ago))

        validator = CooldownRestriction()
        config = {"cooldown_seconds": 3600, "scope": "user"}
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            db=mock_db,
            redis=mock_redis,
            config=config,
        )

        with pytest.raises(Forbidden) as exc_info:
            await validator.check(context)

        detail = str(exc_info.value.detail).lower()
        assert "wait" in detail or "remaining" in detail

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_check_passes_when_cooldown_expired(self):
        from datetime import datetime, timezone, timedelta

        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        now = datetime.now(timezone.utc)
        two_hours_ago = int((now - timedelta(hours=2)).timestamp())
        mock_redis.get = AsyncMock(return_value=str(two_hours_ago))

        validator = CooldownRestriction()
        config = {"cooldown_seconds": 3600, "scope": "user"}
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            db=mock_db,
            redis=mock_redis,
            config=config,
        )

        await validator.check(context)

        mock_redis.set.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_skips_non_target_user(self):
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        validator = CooldownRestriction()
        config = {
            "cooldown_seconds": 3600,
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
        mock_redis.set.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_skips_non_user_scope(self):
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        validator = CooldownRestriction()
        config = {"cooldown_seconds": 3600, "scope": "beatmapset_type"}
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
    def test_config_schema_is_set(self):
        from app.database.schemas.rule import CooldownConfig

        assert CooldownRestriction.config_schema is CooldownConfig


class TestCooldownReserve:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reserve_first_request_sets_and_returns_token(self):
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)  # SET NX succeeded

        validator = CooldownRestriction()
        config = {"cooldown_seconds": 3600, "scope": "user"}
        context = ExecutionContext(queue_id=1, user_id=12345678, db=AsyncMock(), redis=mock_redis)

        token = await validator.reserve(context, config)

        assert token is not None
        mock_redis.set.assert_called_once()
        # NX + EX so the check-and-set is atomic.
        assert mock_redis.set.call_args.kwargs.get("nx") is True
        assert mock_redis.set.call_args.kwargs.get("ex") == 3600

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reserve_when_active_rejects(self):
        from datetime import datetime, timezone, timedelta

        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=None)  # SET NX failed - cooldown active
        thirty_minutes_ago = int((datetime.now(timezone.utc) - timedelta(minutes=30)).timestamp())
        mock_redis.get = AsyncMock(return_value=str(thirty_minutes_ago))

        validator = CooldownRestriction()
        config = {"cooldown_seconds": 3600, "scope": "user"}
        context = ExecutionContext(queue_id=1, user_id=12345678, db=AsyncMock(), redis=mock_redis)

        with pytest.raises(Forbidden):
            await validator.reserve(context, config)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reserve_skips_non_user_scope(self):
        mock_redis = AsyncMock()
        validator = CooldownRestriction()
        config = {"cooldown_seconds": 3600, "scope": "beatmapset_type"}
        context = ExecutionContext(queue_id=1, user_id=12345678, db=AsyncMock(), redis=mock_redis)

        token = await validator.reserve(context, config)

        assert token is None
        mock_redis.set.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_rollback_deletes(self):
        mock_redis = AsyncMock()
        validator = CooldownRestriction()
        context = ExecutionContext(queue_id=1, user_id=12345678, db=AsyncMock(), redis=mock_redis)

        await validator.rollback(context, "some-key")

        mock_redis.delete.assert_called_once_with("some-key")


class TestCooldownRestrictionDetailMessage:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_includes_remaining_time_in_hours_and_minutes(self):
        from datetime import datetime, timezone, timedelta

        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        now = datetime.now(timezone.utc)
        thirty_minutes_ago = int((now - timedelta(minutes=30)).timestamp())
        mock_redis.get = AsyncMock(return_value=str(thirty_minutes_ago))

        validator = CooldownRestriction()
        config = {"cooldown_seconds": 7200, "scope": "user"}
        context = ExecutionContext(
            queue_id=42,
            user_id=12345678,
            db=mock_db,
            redis=mock_redis,
            config=config,
        )

        with pytest.raises(Forbidden) as exc_info:
            await validator.check(context)

        detail = str(exc_info.value.detail)
        assert "1h" in detail
        assert "queue 42" in detail
