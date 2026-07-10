import pytest
from unittest.mock import AsyncMock

from connexion.exceptions import Forbidden

from app.database.rules.validators.blacklist import BlacklistRestriction
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


class TestBlacklistRestriction:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_user_not_blacklisted(self):
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        validator = BlacklistRestriction()
        config = {"scope": "user", "target": [99999999]}
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            db=mock_db,
            redis=mock_redis,
            config=config,
        )

        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_user_blacklisted(self):
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        validator = BlacklistRestriction()
        config = {"scope": "user", "target": [12345678]}
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            db=mock_db,
            redis=mock_redis,
            config=config,
        )

        with pytest.raises(Forbidden) as exc_info:
            await validator.check(context)

        assert "not allowed" in str(exc_info.value.detail).lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_no_target(self):
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        validator = BlacklistRestriction()
        config = {"scope": "user", "target": []}
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            db=mock_db,
            redis=mock_redis,
            config=config,
        )

        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_passes_when_no_target_key(self):
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        validator = BlacklistRestriction()
        config = {"scope": "user"}
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            db=mock_db,
            redis=mock_redis,
            config=config,
        )

        await validator.check(context)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_forbidden_on_violation(self):
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        validator = BlacklistRestriction()
        config = {"scope": "user", "target": [12345678]}
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
        from app.database.schemas.rule import BlacklistConfig

        assert BlacklistRestriction.config_schema is BlacklistConfig

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_includes_queue_id_in_error_message(self):
        mock_db = AsyncMock()
        mock_redis = AsyncMock()

        validator = BlacklistRestriction()
        config = {"scope": "user", "target": [12345678]}
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
        assert "queue 42" in detail
