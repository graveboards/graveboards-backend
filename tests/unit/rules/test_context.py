import pytest
from unittest.mock import AsyncMock, MagicMock

from app.database.rules.context import ExecutionContext
from app.database.rules.exceptions import RuleViolationError


class TestExecutionContext:
    @pytest.mark.unit
    def test_basic_construction(self):
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
        )
        assert context.queue_id == 1
        assert context.user_id == 12345678
        assert context.beatmapset is None
        assert context.beatmaps is None
        assert context.beatmapset_snapshot is None
        assert context.beatmap_snapshots is None
        assert context.db is None
        assert context.redis is None
        assert context.osu_client is None
        assert context.session is None
        assert context.config == {}
        assert context.metadata_providers is None
        assert context._provider_cache == {}

    @pytest.mark.unit
    def test_construction_with_all_fields(self):
        mock_db = AsyncMock()
        mock_redis = AsyncMock()
        mock_osu = AsyncMock()
        mock_session = AsyncMock()
        mock_beatmapset = MagicMock()
        mock_beatmaps = [MagicMock()]
        mock_snapshot = MagicMock()
        mock_snapshots = [MagicMock()]
        providers = {"song_identity": MagicMock}

        context = ExecutionContext(
            queue_id=2,
            user_id=99999999,
            beatmapset=mock_beatmapset,
            beatmaps=mock_beatmaps,
            beatmapset_snapshot=mock_snapshot,
            beatmap_snapshots=mock_snapshots,
            db=mock_db,
            redis=mock_redis,
            osu_client=mock_osu,
            session=mock_session,
            config={"key": "value"},
            metadata_providers=providers,
        )

        assert context.queue_id == 2
        assert context.user_id == 99999999
        assert context.beatmapset is mock_beatmapset
        assert context.beatmaps is mock_beatmaps
        assert context.beatmapset_snapshot is mock_snapshot
        assert context.beatmap_snapshots is mock_snapshots
        assert context.db is mock_db
        assert context.redis is mock_redis
        assert context.osu_client is mock_osu
        assert context.session is mock_session
        assert context.config == {"key": "value"}
        assert context.metadata_providers is providers

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_metadata_caches_result(self):
        mock_provider = AsyncMock()
        mock_provider.resolve = AsyncMock(return_value={"artist": "Test", "title": "Song"})

        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            metadata_providers={"song_identity": lambda: mock_provider},
        )

        result1 = await context.get_metadata("song_identity")
        result2 = await context.get_metadata("song_identity")

        assert result1 == {"artist": "Test", "title": "Song"}
        assert result1 is result2
        mock_provider.resolve.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_metadata_raises_for_unknown_provider(self):
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
            metadata_providers={},
        )

        with pytest.raises(KeyError, match="not registered"):
            await context.get_metadata("nonexistent_provider")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_metadata_raises_when_no_providers(self):
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
        )

        with pytest.raises(KeyError, match="not registered"):
            await context.get_metadata("any_provider")

    @pytest.mark.unit
    def test_invalidate_metadata_clears_all(self):
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
        )
        context._provider_cache["foo"] = {"a": 1}
        context._provider_cache["bar"] = {"b": 2}

        context.invalidate_metadata()

        assert context._provider_cache == {}

    @pytest.mark.unit
    def test_invalidate_metadata_clears_specific(self):
        context = ExecutionContext(
            queue_id=1,
            user_id=12345678,
        )
        context._provider_cache["foo"] = {"a": 1}
        context._provider_cache["bar"] = {"b": 2}

        context.invalidate_metadata("foo")

        assert "foo" not in context._provider_cache
        assert "bar" in context._provider_cache

    @pytest.mark.unit
    def test_config_default_empty_dict(self):
        context = ExecutionContext(queue_id=1, user_id=1)
        assert context.config == {}
        context.config["key"] = "value"
        assert context.config == {"key": "value"}
