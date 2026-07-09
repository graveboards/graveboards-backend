import pytest
from unittest.mock import AsyncMock, MagicMock

from app.database.restrictions.base import (
    RestrictionBase,
    BeatmapRestrictionBase,
    DatabaseRestrictionBase,
)
from app.database.restrictions.context import ExecutionContext
from app.database.restrictions.exceptions import RestrictionViolationError
from app.database.schemas.restriction import RateLimitConfig


class ConcreteRestriction(RestrictionBase):
    restriction_type = "concrete_test"

    async def _check(self, context: ExecutionContext) -> None:
        pass


class ConcreteBeatmapRestriction(BeatmapRestrictionBase):
    restriction_type = "concrete_beatmap_test"

    async def check_beatmap(self, context: ExecutionContext) -> None:
        pass


class ConcreteDatabaseRestriction(DatabaseRestrictionBase):
    restriction_type = "concrete_database_test"

    async def check_database(self, context: ExecutionContext) -> None:
        pass


class TestRestrictionBase:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_config_with_schema(self):
        class TestSchema(RateLimitConfig):
            pass

        class TestRestriction(ConcreteRestriction):
            restriction_type = "test_with_schema"
            config_schema = TestSchema

        restriction = TestRestriction()

        config = {"max_requests": 5, "period": "week", "scope": "user"}
        result = await restriction.validate_config(config)

        assert result["max_requests"] == 5
        assert result["period"] == "week"
        assert result["scope"] == "user"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_config_without_schema(self):
        class TestRestriction(ConcreteRestriction):
            restriction_type = "test_without_schema"

        restriction = TestRestriction()

        config = {"arbitrary": "data"}
        result = await restriction.validate_config(config)

        assert result == {"arbitrary": "data"}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_check_raises_when_no_config(self):
        restriction = ConcreteRestriction()
        context = ExecutionContext(queue_id=1, user_id=1)

        with pytest.raises(RestrictionViolationError) as exc_info:
            await restriction.check(context)

        assert exc_info.value.restriction_type == "concrete_test"
        assert "Missing configuration" in str(exc_info.value.detail)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_check_delegates_to_check_method(self):
        call_log = []

        class LoggingRestriction(RestrictionBase):
            restriction_type = "logging_test"

            async def _check(self, context: ExecutionContext) -> None:
                call_log.append(context.queue_id)

        restriction = LoggingRestriction()
        context = ExecutionContext(
            queue_id=42,
            user_id=1,
            config={"key": "value"},
        )

        await restriction.check(context)

        assert call_log == [42]


class TestBeatmapRestrictionBase:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_no_beatmapset(self):
        restriction = ConcreteBeatmapRestriction()
        context = ExecutionContext(
            queue_id=1,
            user_id=1,
            config={"key": "value"},
        )

        with pytest.raises(RestrictionViolationError) as exc_info:
            await restriction.check(context)

        assert exc_info.value.restriction_type == "concrete_beatmap_test"
        assert "Beatmapset metadata not available" in str(exc_info.value.detail)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delegates_to_check_beatmap_when_beatmapset_present(self):
        call_log = []
        mock_beatmapset = MagicMock()

        class LoggingBeatmapRestriction(BeatmapRestrictionBase):
            restriction_type = "logging_beatmap_test"

            async def check_beatmap(self, context: ExecutionContext) -> None:
                call_log.append(context.beatmapset.id)

        restriction = LoggingBeatmapRestriction()
        context = ExecutionContext(
            queue_id=1,
            user_id=1,
            config={"key": "value"},
            beatmapset=mock_beatmapset,
        )

        await restriction.check(context)

        assert call_log == [mock_beatmapset.id]


class TestDatabaseRestrictionBase:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_when_no_osu_client(self):
        restriction = ConcreteDatabaseRestriction()
        context = ExecutionContext(
            queue_id=1,
            user_id=1,
            config={"key": "value"},
        )

        with pytest.raises(RestrictionViolationError) as exc_info:
            await restriction.check(context)

        assert exc_info.value.restriction_type == "concrete_database_test"
        assert "osu! API access" in str(exc_info.value.detail)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delegates_to_check_database_when_osu_client_present(self):
        call_log = []
        mock_osu = AsyncMock()

        class LoggingDatabaseRestriction(DatabaseRestrictionBase):
            restriction_type = "logging_database_test"

            async def check_database(self, context: ExecutionContext) -> None:
                call_log.append(context.osu_client is mock_osu)

        restriction = LoggingDatabaseRestriction()
        context = ExecutionContext(
            queue_id=1,
            user_id=1,
            config={"key": "value"},
            osu_client=mock_osu,
        )

        await restriction.check(context)

        assert call_log == [True]


class TestConfigSchema:
    @pytest.mark.unit
    def test_rate_limit_config_schema(self):
        from app.database.restrictions.validators.rate_limit import RateLimitRestriction

        assert RateLimitRestriction.config_schema is RateLimitConfig

    @pytest.mark.unit
    def test_cooldown_config_schema(self):
        from app.database.restrictions.validators.cooldown import CooldownRestriction
        from app.database.schemas.restriction import CooldownConfig

        assert CooldownRestriction.config_schema is CooldownConfig

    @pytest.mark.unit
    def test_blacklist_config_schema(self):
        from app.database.restrictions.validators.blacklist import BlacklistRestriction
        from app.database.schemas.restriction import BlacklistConfig

        assert BlacklistRestriction.config_schema is BlacklistConfig
