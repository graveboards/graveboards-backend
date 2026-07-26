import pytest

from app.exceptions import DeepObjectValidationError
from app.patches.validators.include import validate_include


class TestIncludeValidator:
    """Test include parameter validation."""

    def test_validate_include_boolean_true(self) -> None:
        """Test validation of boolean true."""
        schema = {"properties": {"user": {"type": "boolean"}}}
        include = {"user": True}

        validate_include(include, schema)

    def test_validate_include_boolean_false(self) -> None:
        """Test validation of boolean false."""
        schema = {"properties": {"user": {"type": "boolean"}}}
        include = {"user": False}

        result = validate_include(include, schema)

        assert result is None

    def test_validate_include_nested_object(self) -> None:
        """Test validation of nested object."""
        schema = {
            "properties": {
                "user": {"type": "object", "properties": {"profile": {"type": "boolean"}}}
            }
        }
        include = {"user": {"profile": True}}

        validate_include(include, schema)

    def test_validate_include_unknown_field_raises(self) -> None:
        """Test that unknown fields raise error."""
        schema = {"properties": {"user": {"type": "boolean"}}}
        include = {"unknown": True}

        with pytest.raises(DeepObjectValidationError):
            validate_include(include, schema)

    def test_validate_include_expected_boolean_raises(self) -> None:
        """Test that non-boolean value raises error."""
        schema = {"properties": {"user": {"type": "boolean"}}}
        include = {"user": "not_a_boolean"}

        with pytest.raises(DeepObjectValidationError):
            validate_include(include, schema)

    def test_validate_include_nested_include_not_allowed_raises(self) -> None:
        """Test that nested include where not allowed raises error."""
        schema = {
            "properties": {
                "user": {"oneOf": [{"type": "boolean"}, {"type": "object", "properties": {}}]}
            }
        }
        include = {"user": {"nested": True}}

        with pytest.raises(DeepObjectValidationError):
            validate_include(include, schema)

    def test_validate_include_boolean_allowed_in_oneof(self) -> None:
        """Test that boolean is allowed where object is optional in oneOf."""
        schema = {
            "properties": {
                "user": {
                    "oneOf": [
                        {"type": "boolean"},
                        {"type": "object", "properties": {"profile": {"type": "boolean"}}},
                    ]
                }
            }
        }
        include = {"user": True}

        validate_include(include, schema)

    def test_validate_include_expected_nested_object_raises(self) -> None:
        """Test that non-object value raises error for object type."""
        schema = {"properties": {"user": {"type": "object"}}}
        include = {"user": "not_an_object"}

        with pytest.raises(DeepObjectValidationError):
            validate_include(include, schema)

    def test_validate_include_expected_boolean_or_object_raises(self) -> None:
        """Test that invalid type raises error."""
        schema = {"properties": {"user": {"oneOf": [{"type": "boolean"}, {"type": "object"}]}}}
        include = {"user": 123}

        with pytest.raises(DeepObjectValidationError):
            validate_include(include, schema)

    def test_validate_include_deep_nesting(self) -> None:
        """Test validation of deeply nested includes."""
        schema = {
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "profile": {
                            "type": "object",
                            "properties": {"settings": {"type": "boolean"}},
                        }
                    },
                }
            }
        }
        include = {"user": {"profile": {"settings": True}}}

        validate_include(include, schema)

    def test_validate_include_multiple_fields(self) -> None:
        """Test validation of multiple include fields."""
        schema = {"properties": {"user": {"type": "boolean"}, "beatmaps": {"type": "boolean"}}}
        include = {"user": True, "beatmaps": False}

        validate_include(include, schema)

    def test_validate_include_empty_include(self) -> None:
        """Test validation of empty include."""
        schema: dict[str, dict[str, object]] = {"properties": {"user": {"type": "boolean"}}}
        include: dict[str, object] = {}

        validate_include(include, schema)

    def test_validate_include_with_path_tracking(self) -> None:
        """Test that path tracking works correctly."""
        schema = {
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "profile": {
                            "type": "object",
                            "properties": {"settings": {"type": "boolean"}},
                        }
                    },
                }
            }
        }
        include = {"user": {"profile": {"settings": True}}}

        validate_include(include, schema)

    def test_validate_include_enum_boolean_restriction(self) -> None:
        """Test validation with enum restriction on boolean."""
        schema = {"properties": {"user": {"type": "boolean", "enum": [True]}}}
        include = {"user": True}

        validate_include(include, schema)

    def test_validate_include_enum_false_restriction_raises(self) -> None:
        """Test that enum False restriction rejects True."""
        schema = {"properties": {"user": {"type": "boolean", "enum": [False]}}}
        include = {"user": True}

        with pytest.raises(DeepObjectValidationError):
            validate_include(include, schema)

    def test_validate_include_schema_definition_error(self) -> None:
        """Test that invalid schema raises error."""
        schema = {"properties": {"user": {"type": "invalid_type"}}}
        include = {"user": True}

        with pytest.raises(DeepObjectValidationError):
            validate_include(include, schema)
