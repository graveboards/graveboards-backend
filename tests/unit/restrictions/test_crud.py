import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.database.crud.restrictions import RestrictionCRUD, _normalize_config
from app.exceptions import Conflict


class TestNormalizeConfig:
    @pytest.mark.unit
    def test_identical_configs_produce_same_key(self):
        a = {"max_requests": 5, "period": "week", "scope": "user"}
        b = {"scope": "user", "period": "week", "max_requests": 5}
        assert _normalize_config(a) == _normalize_config(b)

    @pytest.mark.unit
    def test_different_configs_produce_different_keys(self):
        a = {"max_requests": 5, "period": "week"}
        b = {"max_requests": 10, "period": "week"}
        assert _normalize_config(a) != _normalize_config(b)

    @pytest.mark.unit
    def test_sorted_list_values(self):
        a = {"target": [3, 1, 2]}
        b = {"target": [1, 2, 3]}
        assert _normalize_config(a) == _normalize_config(b)

    @pytest.mark.unit
    def test_nested_dicts_are_sorted(self):
        a = {"outer": {"z": 1, "a": 2}}
        b = {"outer": {"a": 2, "z": 1}}
        assert _normalize_config(a) == _normalize_config(b)

    @pytest.mark.unit
    def test_empty_configs_match(self):
        assert _normalize_config({}) == _normalize_config({})

    @pytest.mark.unit
    def test_missing_keys_produce_different_keys_than_explicit_none(self):
        a = {"scope": "user"}
        b = {"scope": "user", "target": None}
        assert _normalize_config(a) != _normalize_config(b)


class TestUpsertRestrictionsDuplicateDetection:
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_on_duplicate_blacklist_entries(self):
        crud = RestrictionCRUD()
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        restrictions_data = [
            {
                "restriction_type": "blacklist",
                "config": {"scope": "user", "target": [12345]},
            },
            {
                "restriction_type": "blacklist",
                "config": {"scope": "user", "target": [12345]},
            },
        ]

        with pytest.raises(Conflict):
            await crud.upsert_restrictions(
                queue_id=1,
                restrictions_data=restrictions_data,
                session=mock_session,
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_raises_on_duplicate_rate_limit_entries(self):
        crud = RestrictionCRUD()
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        restrictions_data = [
            {
                "restriction_type": "rate_limit",
                "config": {"max_requests": 5, "period": "week", "scope": "user"},
            },
            {
                "restriction_type": "rate_limit",
                "config": {"period": "week", "max_requests": 5, "scope": "user"},
            },
        ]

        with pytest.raises(Conflict):
            await crud.upsert_restrictions(
                queue_id=1,
                restrictions_data=restrictions_data,
                session=mock_session,
            )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_allows_similar_but_different_configs(self):
        crud = RestrictionCRUD()
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))))
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.add = AsyncMock()

        restrictions_data = [
            {
                "restriction_type": "rate_limit",
                "config": {"max_requests": 5, "period": "week", "scope": "user"},
            },
            {
                "restriction_type": "rate_limit",
                "config": {"max_requests": 10, "period": "week", "scope": "user"},
            },
        ]

        result = await crud.upsert_restrictions(
            queue_id=1,
            restrictions_data=restrictions_data,
            session=mock_session,
        )

        assert len(result) == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_allows_same_type_different_configs(self):
        crud = RestrictionCRUD()
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))))
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.add = AsyncMock()

        restrictions_data = [
            {
                "restriction_type": "blacklist",
                "config": {"scope": "user", "target": [111]},
            },
            {
                "restriction_type": "blacklist",
                "config": {"scope": "user", "target": [222]},
            },
        ]

        result = await crud.upsert_restrictions(
            queue_id=1,
            restrictions_data=restrictions_data,
            session=mock_session,
        )

        assert len(result) == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_allows_different_types_with_same_config(self):
        crud = RestrictionCRUD()
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))))
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.add = AsyncMock()

        restrictions_data = [
            {
                "restriction_type": "rate_limit",
                "config": {"max_requests": 5, "period": "week"},
            },
            {
                "restriction_type": "cooldown",
                "config": {"cooldown_seconds": 300},
            },
        ]

        result = await crud.upsert_restrictions(
            queue_id=1,
            restrictions_data=restrictions_data,
            session=mock_session,
        )

        assert len(result) == 2
