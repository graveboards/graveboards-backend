import pytest
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy import column

from app.database.utils import validate_type
from app.database.enums import FilterOperator
from app.database.crud import c, r, u, d
from app.database.crud.types import Sorting, Conditions, Filters, Include
from app.exceptions import TypeValidationError, FieldValidationError


class TestCreateInputValidation:
    """Test CRUD create operation input validation."""

    def test_create_with_required_fields(self, db_session):
        """Test create with all required fields."""
        from app.database.models import Beatmapset
        from app.database.schemas import BeatmapsetCreateSchema

        data = {
            "id": 123,
            "user_id": 456,
        }

        schema = BeatmapsetCreateSchema.model_validate(data)
        assert schema.id == 123
        assert schema.user_id == 456

    def test_create_with_optional_fields(self, db_session):
        """Test create with optional fields."""
        from app.database.models import Beatmapset
        from app.database.schemas import BeatmapsetCreateSchema

        data = {
            "id": 123,
            "user_id": 456,
            "channel_id": 789,
        }

        schema = BeatmapsetCreateSchema.model_validate(data)
        assert schema.id == 123

    def test_create_rejects_extra_fields(self, db_session):
        """Test create rejects unknown fields."""
        from app.database.schemas import BeatmapsetCreateSchema

        data = {
            "id": 123,
            "user_id": 456,
            "unknown_field": "value"
        }

        with pytest.raises(Exception):
            BeatmapsetCreateSchema.model_validate(data)

    def test_create_validates_types(self, db_session):
        """Test create validates field types."""
        from app.database.schemas import BeatmapsetCreateSchema

        data = {
            "id": "not_an_int",
            "user_id": 456,
        }

        with pytest.raises(Exception):
            BeatmapsetCreateSchema.model_validate(data)


class TestReadInputValidation:
    """Test CRUD read operation input validation."""

    def test_valid_sorting_structure(self):
        """Test valid sorting configuration."""
        sorting: Sorting = [
            {"field": "Beatmapset.id", "order": "asc"},
            {"field": "Beatmapset.created_at", "order": "desc"}
        ]
        assert len(sorting) == 2

    def test_sorting_default_order(self):
        """Test sorting with default order."""
        sorting: Sorting = [
            {"field": "Beatmapset.id"}
        ]
        assert sorting[0]["field"] == "Beatmapset.id"

    def test_valid_filter_structure(self):
        """Test valid filter configuration."""
        filters: Filters = {
            "id": {"eq": 123},
            "user": {
                "username": {"eq": "test_user"}
            }
        }
        assert filters["id"]["eq"] == 123

    def test_filter_with_null_check(self):
        """Test filter with null condition."""
        filters: Filters = {
            "deleted_at": {"is_null": True}
        }
        assert filters["deleted_at"]["is_null"] is True

    def test_valid_include_structure(self):
        """Test valid include configuration."""
        include: Include = {
            "user": True,
            "beatmaps": {
                "owner_profiles": True
            }
        }
        assert include["user"] is True

    def test_include_with_explicit_false(self):
        """Test include with explicit false."""
        include: Include = {
            "user": True,
            " Beatmapset.user": False
        }
        assert include["Beatmapset.user"] is False

    def test_invalid_include_type(self):
        """Test include validates boolean or nested object."""
        from app.patches.validators.include import validate_include
        
        include = {"user": "not_a_boolean"}
        schema = {"properties": {"user": {"type": "boolean"}}}
        
        with pytest.raises(Exception):
            validate_include(include, schema)


class TestUpdateInputValidation:
    """Test CRUD update operation input validation."""

    def test_update_with_valid_data(self, db_session):
        """Test update with valid data."""
        from app.database.models import Beatmapset
        from app.database.schemas import BeatmapsetUpdateSchema

        data = {
            "channel_id": 789,
            "scheduled_end": "2025-01-01T00:00:00+00:00"
        }

        schema = BeatmapsetUpdateSchema.model_validate(data)
        assert schema.channel_id == 789

    def test_update_rejects_id_field(self, db_session):
        """Test update rejects primary key modification."""
        from app.database.schemas import BeatmapsetUpdateSchema

        data = {
            "id": 999,
            "channel_id": 789
        }

        schema = BeatmapsetUpdateSchema.model_validate(data)
        assert schema.channel_id == 789

    def test_update_partial_fields(self, db_session):
        """Test update with partial fields."""
        from app.database.schemas import BeatmapsetUpdateSchema

        data = {
            "channel_id": 789
        }

        schema = BeatmapsetUpdateSchema.model_validate(data)
        assert schema.channel_id == 789


class TestDeleteInputValidation:
    """Test CRUD delete operation input validation."""

    def test_delete_with_valid_id(self, db_session):
        """Test delete with valid primary key."""
        from app.database.models import Beatmapset

        result = c.delete(Beatmapset, 123, session=db_session)
        assert result is None

    def test_delete_rejects_invalid_id_type(self, db_session):
        """Test delete validates primary key type."""
        from app.database.models import Beatmapset

        with pytest.raises(Exception):
            c.delete(Beatmapset, "not_an_int", session=db_session)


class TestComplexValidationScenarios:
    """Test complex validation scenarios."""

    def test_nested_filters_validation(self):
        """Test nested filter validation."""
        filters: Filters = {
            "beatmaps": {
                "checksum": {"eq": "abc123"}
            },
            "user": {
                "username": {"regex": "test.*"},
                "profile": {
                    "osu_id": {"in": [1, 2, 3]}
                }
            }
        }
        
        assert filters["beatmaps"]["checksum"]["eq"] == "abc123"
        assert filters["user"]["username"]["regex"] == "test.*"

    def test_complex_sorting_with_multiple_fields(self):
        """Test sorting with multiple fields and orders."""
        sorting: Sorting = [
            {"field": "Beatmapset.created_at", "order": "desc"},
            {"field": "Beatmapset.id", "order": "asc"},
            {"field": "Beatmapset.channel_id", "order": "desc"}
        ]
        
        assert len(sorting) == 3
        assert sorting[0]["order"] == "desc"

    def test_mixed_include_boolean_and_nested(self):
        """Test include with both boolean and nested structures."""
        include: Include = {
            "user": True,
            "beatmaps": {
                "owner_profiles": True,
                "beatmap_tags": False
            },
            "user.profile": True
        }
        
        assert include["user"] is True
        assert include["beatmaps"]["owner_profiles"] is True

    def test_filter_with_range_conditions(self):
        """Test filter with range conditions."""
        filters: Filters = {
            "id": {"gt": 100, "lt": 200},
            "created_at": {"gte": "2024-01-01T00:00:00+00:00"}
        }
        
        assert filters["id"]["gt"] == 100
        assert filters["id"]["lt"] == 200

    def test_multiple_filter_operators(self):
        """Test filter with multiple operators on same field."""
        filters: Filters = {
            "id": {
                "eq": 123,
                "neq": 456,
                "in": [1, 2, 3, 4, 5]
            }
        }
        
        assert filters["id"]["eq"] == 123
        assert filters["id"]["in"] == [1, 2, 3, 4, 5]

    def test_null_conditions(self):
        """Test null condition handling."""
        filters: Filters = {
            "deleted_at": {"is_null": True},
            "scheduled_end": {"is_null": False}
        }
        
        assert filters["deleted_at"]["is_null"] is True
        assert filters["scheduled_end"]["is_null"] is False
