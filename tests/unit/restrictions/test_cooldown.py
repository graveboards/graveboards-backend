import pytest
from unittest.mock import AsyncMock

from connexion.exceptions import Forbidden

from app.database.restrictions.validators.cooldown import (
    CooldownRestriction,
)


class TestCooldownRestriction:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_on_first_request(self):
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.expire = AsyncMock(return_value=True)

        validator = CooldownRestriction()
        config = {"cooldown_seconds": 3600, "scope": "user"}

        await validator.check(
            queue_id=1,
            user_id=12345678,
            db=mock_db,
            redis=mock_redis,
            config=config,
        )

        mock_redis.get.assert_called_once()
        mock_redis.set.assert_called_once()
        mock_redis.expire.assert_called_once()

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

        with pytest.raises(Forbidden) as exc_info:
            await validator.check(
                queue_id=1,
                user_id=12345678,
                db=mock_db,
                redis=mock_redis,
                config=config,
            )

        detail = str(exc_info.value.detail).lower()
        assert "wait" in detail or "remaining" in detail

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_cooldown_expired(self):
        from datetime import datetime, timezone, timedelta

        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.expire = AsyncMock(return_value=True)

        now = datetime.now(timezone.utc)
        two_hours_ago = int((now - timedelta(hours=2)).timestamp())
        mock_redis.get = AsyncMock(return_value=str(two_hours_ago))

        validator = CooldownRestriction()
        config = {"cooldown_seconds": 3600, "scope": "user"}

        await validator.check(
            queue_id=1,
            user_id=12345678,
            db=mock_db,
            redis=mock_redis,
            config=config,
        )

        mock_redis.set.assert_called_once()

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

        await validator.check(
            queue_id=1,
            user_id=12345678,
            db=mock_db,
            redis=mock_redis,
            config=config,
        )

        mock_redis.get.assert_not_called()
        mock_redis.set.assert_not_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_skips_non_user_scope(self):
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        validator = CooldownRestriction()
        config = {"cooldown_seconds": 3600, "scope": "beatmapset_type"}

        await validator.check(
            queue_id=1,
            user_id=12345678,
            db=mock_db,
            redis=mock_redis,
            config=config,
        )

        mock_redis.get.assert_not_called()
