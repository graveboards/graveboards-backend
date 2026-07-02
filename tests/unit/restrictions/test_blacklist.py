import pytest
from unittest.mock import AsyncMock

from app.database.restrictions.validators.blacklist import BlacklistRestriction


class TestBlacklistRestriction:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_user_not_blacklisted(self):
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        validator = BlacklistRestriction()
        config = {"scope": "user", "target": [99999999]}

        await validator.check(
            queue_id=1,
            user_id=12345678,
            db=mock_db,
            redis=mock_redis,
            config=config,
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_user_blacklisted(self):
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        validator = BlacklistRestriction()
        config = {"scope": "user", "target": [12345678]}

        with pytest.raises(Exception) as exc_info:
            await validator.check(
                queue_id=1,
                user_id=12345678,
                db=mock_db,
                redis=mock_redis,
                config=config,
            )

        assert "not allowed" in str(exc_info.value.detail).lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_no_target(self):
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        validator = BlacklistRestriction()
        config = {"scope": "user", "target": []}

        await validator.check(
            queue_id=1,
            user_id=12345678,
            db=mock_db,
            redis=mock_redis,
            config=config,
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_no_target_key(self):
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        validator = BlacklistRestriction()
        config = {"scope": "user"}

        await validator.check(
            queue_id=1,
            user_id=12345678,
            db=mock_db,
            redis=mock_redis,
            config=config,
        )
