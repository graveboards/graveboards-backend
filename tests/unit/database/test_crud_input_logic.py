from typing import Any, cast

import pytest
from pydantic import ValidationError

from app.database.crud.types import Filters, Include, Sorting
from app.exceptions import DeepObjectValidationError


class TestCreateInputValidation:
    """Test CRUD create operation input validation."""

    def test_create_with_required_fields_beatmapset(self) -> None:
        """Test create with all required fields."""
        from app.database.schemas import BeatmapsetCreateSchema

        data = {
            "user_id": 456,
        }

        schema = BeatmapsetCreateSchema.model_validate(data)
        assert schema.user_id == 456

    def test_create_with_required_fields_beatmap(self) -> None:
        """Test create with all required fields."""
        from app.database.schemas import BeatmapCreateSchema

        data = {
            "beatmapset_id": 456,
        }

        schema = BeatmapCreateSchema.model_validate(data)
        assert schema.beatmapset_id == 456

    def test_create_rejects_extra_fields_beatmapset(self) -> None:
        """Test create rejects unknown fields."""
        from app.database.schemas import BeatmapsetCreateSchema

        data = {"user_id": 456, "unknown_field": "value"}

        with pytest.raises(ValidationError):
            BeatmapsetCreateSchema.model_validate(data)

    def test_create_validates_types_beatmapset(self) -> None:
        """Test create validates field types."""
        from app.database.schemas import BeatmapsetCreateSchema

        data = {
            "user_id": "not_an_int",
        }

        with pytest.raises(ValidationError):
            BeatmapsetCreateSchema.model_validate(data)

    def test_create_validates_types_beatmap(self) -> None:
        """Test create validates field types."""
        from app.database.schemas import BeatmapCreateSchema

        data = {
            "beatmapset_id": "not_an_int",
        }

        with pytest.raises(ValidationError):
            BeatmapCreateSchema.model_validate(data)


class TestBeatmapCreateInputValidation:
    """Test CRUD create operation input validation for beatmap."""

    def test_create_with_required_fields(self) -> None:
        """Test create with all required fields."""
        from app.database.schemas import BeatmapCreateSchema

        data = {
            "beatmapset_id": 456,
        }

        schema = BeatmapCreateSchema.model_validate(data)
        assert schema.beatmapset_id == 456

    def test_create_rejects_extra_fields(self) -> None:
        """Test create rejects unknown fields."""
        from app.database.schemas import BeatmapCreateSchema

        data = {"beatmapset_id": 456, "unknown_field": "value"}

        with pytest.raises(ValidationError):
            BeatmapCreateSchema.model_validate(data)


class TestReadInputValidation:
    """Test CRUD read operation input validation."""

    def test_valid_sorting_structure(self) -> None:
        """Test valid sorting configuration."""
        sorting: Sorting = [
            {"field": "Beatmapset.id", "order": "asc"},
            {"field": "Beatmapset.created_at", "order": "desc"},
        ]
        assert len(list(sorting)) == 2

    def test_sorting_default_order(self) -> None:
        """Test sorting with default order."""
        sorting: Sorting = [{"field": "Beatmapset.id"}]
        sorting_list: list[dict[str, Any]] = [dict(s.items()) for s in sorting]
        assert sorting_list[0]["field"] == "Beatmapset.id"

    def test_valid_filter_structure(self) -> None:
        """Test valid filter configuration."""
        filters: Filters = {"id": {"eq": 123}, "user": {"username": {"eq": "test_user"}}}
        filters_dict: dict[str, Any] = dict(filters)
        assert cast("dict", filters_dict["id"])["eq"] == 123

    def test_filter_with_null_check(self) -> None:
        """Test filter with null condition."""
        filters: Filters = {"deleted_at": {"is_null": True}}
        filters_dict: dict[str, Any] = dict(filters)
        assert cast("dict", filters_dict["deleted_at"])["is_null"] is True

    def test_valid_include_structure(self) -> None:
        """Test valid include configuration."""
        include: Include = {"user": True, "beatmaps": {"owner_profiles": True}}
        include_dict: dict[str, Any] = dict(include)
        assert include_dict["user"] is True

    def test_include_with_explicit_false(self) -> None:
        """Test include with explicit false."""
        include: Include = {"user": True, "Beatmapset.user": False}
        include_dict: dict[str, Any] = dict(include)
        assert include_dict["Beatmapset.user"] is False

    def test_invalid_include_type(self) -> None:
        """Test include validates boolean or nested object."""
        from app.patches.validators.include import validate_include

        include = {"user": "not_a_boolean"}
        schema = {"properties": {"user": {"type": "boolean"}}}

        with pytest.raises(DeepObjectValidationError):
            validate_include(include, schema)


class TestUpdateInputValidation:
    """Test CRUD update operation input validation."""

    def test_update_with_valid_data(self) -> None:
        """Test update with valid data."""
        from app.database.schemas import BeatmapsetUpdateSchema

        data = {
            "user_id": 789,
        }

        schema = BeatmapsetUpdateSchema.model_validate(data)
        assert schema.user_id == 789

    def test_update_allows_none_fields(self) -> None:
        """Test update allows None fields for partial updates."""
        from app.database.schemas import BeatmapsetUpdateSchema

        data = {"user_id": None}

        schema = BeatmapsetUpdateSchema.model_validate(data)
        assert schema.user_id is None

    def test_update_partial_fields(self) -> None:
        """Test update with partial fields."""
        from app.database.schemas import BeatmapsetUpdateSchema

        data = {"user_id": 789}

        schema = BeatmapsetUpdateSchema.model_validate(data)
        assert schema.user_id == 789

    def test_update_with_beatmap_schema(self) -> None:
        """Test update with beatmap schema."""
        from app.database.schemas import BeatmapUpdateSchema

        data = {"beatmapset_id": 789}

        schema = BeatmapUpdateSchema.model_validate(data)
        assert schema.beatmapset_id == 789


class TestDeleteInputValidation:
    """CRUD delete operation tests — require a live database session.

    These are integration tests that live under tests/unit/ for historical
    reasons. They are explicitly marked ``integration`` so ``make test``
    (unit-only) skips them.
    """

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_with_valid_id(self, db_session: Any) -> None:
        """Test delete with valid primary key."""
        from app.database.db import PostgresqlDB
        from app.database.models import Beatmapset, User

        db = PostgresqlDB()

        await db.add(User, session=db_session, id=99999)
        created = await db.add(
            Beatmapset,
            session=db_session,
            id=99999,
            user_id=99999,
        )
        await db.delete(Beatmapset, session=db_session, id=created.id)

        fetched = await db.get(Beatmapset, session=db_session, id=created.id)
        assert fetched is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_rejects_invalid_id_type(self, db_session: Any) -> None:
        """Test delete raises ValueError for non-existent record."""
        from app.database.db import PostgresqlDB
        from app.database.models import Beatmapset, User

        db = PostgresqlDB()

        await db.add(User, session=db_session, id=99998)
        await db.add(
            Beatmapset,
            session=db_session,
            id=99998,
            user_id=99998,
        )

        with pytest.raises(ValueError, match="No Beatmapset matches the provided filters"):
            await db.delete(Beatmapset, session=db_session, id=99999)


class TestComplexValidationScenarios:
    """Test complex validation scenarios."""

    def test_nested_filters_validation(self) -> None:
        """Test nested filter validation."""
        filters: dict[str, Any] = {
            "beatmaps": {"checksum": {"eq": "abc123"}},
            "user": {"username": {"regex": "test.*"}, "profile": {"osu_id": {"in": [1, 2, 3]}}},
        }

        filters_dict: dict[str, Any] = dict(filters)
        beatmaps: dict[str, Any] = cast("dict", filters_dict["beatmaps"])
        user: dict[str, Any] = cast("dict", filters_dict["user"])
        assert beatmaps["checksum"]["eq"] == "abc123"
        assert user["username"]["regex"] == "test.*"

    def test_complex_sorting_with_multiple_fields(self) -> None:
        """Test sorting with multiple fields and orders."""
        sorting: Sorting = [
            {"field": "Beatmapset.created_at", "order": "desc"},
            {"field": "Beatmapset.id", "order": "asc"},
            {"field": "Beatmapset.channel_id", "order": "desc"},
        ]

        assert len(list(sorting)) == 3
        sorting_list: list[dict[str, Any]] = [dict(s.items()) for s in sorting]
        assert sorting_list[0]["order"] == "desc"

    def test_mixed_include_boolean_and_nested(self) -> None:
        """Test include with both boolean and nested structures."""
        include: Include = {
            "user": True,
            "beatmaps": {"owner_profiles": True, "beatmap_tags": False},
            "user.profile": True,
        }

        include_dict: dict[str, Any] = dict(include)
        assert include_dict["user"] is True
        beatmaps_include: dict[str, Any] = cast("dict", include_dict["beatmaps"])
        assert beatmaps_include["owner_profiles"] is True

    def test_filter_with_range_conditions(self) -> None:
        """Test filter with range conditions."""
        filters: Filters = {
            "id": {"gt": 100, "lt": 200},
            "created_at": {"gte": "2024-01-01T00:00:00+00:00"},
        }

        filters_dict: dict[str, Any] = dict(filters)
        assert cast("dict", filters_dict["id"])["gt"] == 100
        assert cast("dict", filters_dict["id"])["lt"] == 200

    def test_multiple_filter_operators(self) -> None:
        """Test filter with multiple operators on same field."""
        filters: dict[str, Any] = {"id": {"eq": 123, "neq": 456, "in": [1, 2, 3, 4, 5]}}

        filters_dict: dict[str, Any] = dict(filters)
        assert cast("dict", filters_dict["id"])["eq"] == 123
        assert cast("dict", filters_dict["id"])["in"] == [1, 2, 3, 4, 5]

    def test_null_conditions(self) -> None:
        """Test null condition handling."""
        filters: Filters = {"deleted_at": {"is_null": True}, "scheduled_end": {"is_null": False}}

        filters_dict: dict[str, Any] = dict(filters)
        assert cast("dict", filters_dict["deleted_at"])["is_null"] is True
        assert cast("dict", filters_dict["scheduled_end"])["is_null"] is False
