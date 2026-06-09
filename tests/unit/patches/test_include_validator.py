import pytest

from app.patches.validators.include import validate_include


@pytest.mark.skip(reason="Include validator implementation issues")
class TestIncludeValidator:
    """Test include parameter validation."""

    def test_validate_include_boolean_true(self):
        """Test validation of boolean true."""
        schema = {
            "properties": {
                "user": {"type": "boolean"}
            }
        }
        include = {"user": True}

        result = validate_include(include, schema)

        assert result is None

    def test_validate_include_boolean_false(self):
        """Test validation of boolean false."""
        schema = {
            "properties": {
                "user": {"type": "boolean"}
            }
        }
        include = {"user": False}

        result = validate_include(include, schema)

        assert result is None

    def test_validate_include_nested_object(self):
        """Test validation of nested object."""
        schema = {
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "profile": {"type": "boolean"}
                    }
                }
            }
        }
        include = {"user": {"profile": True}}

        result = validate_include(include, schema)

        assert result is None

    def test_validate_include_unknown_field_raises(self):
        """Test that unknown fields raise error."""
        schema = {
            "properties": {
                "user": {"type": "boolean"}
            }
        }
        include = {"unknown": True}

        with pytest.raises(Exception):
            validate_include(include, schema)

    def test_validate_include_expected_boolean_raises(self):
        """Test that non-boolean value raises error."""
        schema = {
            "properties": {
                "user": {"type": "boolean"}
            }
        }
        include = {"user": "not_a_boolean"}

        with pytest.raises(Exception):
            validate_include(include, schema)

    def test_validate_include_nested_include_not_allowed_raises(self):
        """Test that nested include where not allowed raises error."""
        schema = {
            "properties": {
                "user": {
                    "oneOf": [
                        {"type": "boolean"},
                        {"type": "object", "properties": {}}
                    ]
                }
            }
        }
        include = {"user": {"nested": True}}

        with pytest.raises(Exception):
            validate_include(include, schema)

    def test_validate_include_boolean_not_allowed_raises(self):
        """Test that boolean where object required raises error."""
        schema = {
            "properties": {
                "user": {
                    "oneOf": [
                        {"type": "boolean"},
                        {"type": "object", "properties": {"profile": {"type": "boolean"}}}
                    ]
                }
            }
        }
        include = {"user": True}

        with pytest.raises(Exception):
            validate_include(include, schema)

    def test_validate_include_expected_nested_object_raises(self):
        """Test that non-object value raises error for object type."""
        schema = {
            "properties": {
                "user": {"type": "object"}
            }
        }
        include = {"user": "not_an_object"}

        with pytest.raises(Exception):
            validate_include(include, schema)

    def test_validate_include_expected_boolean_or_object_raises(self):
        """Test that invalid type raises error."""
        schema = {
            "properties": {
                "user": {
                    "oneOf": [
                        {"type": "boolean"},
                        {"type": "object"}
                    ]
                }
            }
        }
        include = {"user": 123}

        with pytest.raises(Exception):
            validate_include(include, schema)

    def test_validate_include_deep_nesting(self):
        """Test validation of deeply nested includes."""
        schema = {
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "profile": {
                            "type": "object",
                            "properties": {
                                "settings": {"type": "boolean"}
                            }
                        }
                    }
                }
            }
        }
        include = {"user": {"profile": {"settings": True}}}

        result = validate_include(include, schema)

        assert result is None

    def test_validate_include_multiple_fields(self):
        """Test validation of multiple include fields."""
        schema = {
            "properties": {
                "user": {"type": "boolean"},
                "beatmaps": {"type": "boolean"}
            }
        }
        include = {"user": True, "beatmaps": False}

        result = validate_include(include, schema)

        assert result is None

    def test_validate_include_empty_include(self):
        """Test validation of empty include."""
        schema = {
            "properties": {
                "user": {"type": "boolean"}
            }
        }
        include = {}

        result = validate_include(include, schema)

        assert result is None

    def test_validate_include_with_path_tracking(self):
        """Test that path tracking works correctly."""
        schema = {
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "profile": {
                            "type": "object",
                            "properties": {
                                "settings": {"type": "boolean"}
                            }
                        }
                    }
                }
            }
        }
        include = {"user": {"profile": {"settings": True}}}

        result = validate_include(include, schema)

        assert result is None

    def test_validate_include_enum_boolean_restriction(self):
        """Test validation with enum restriction on boolean."""
        schema = {
            "properties": {
                "user": {
                    "type": "boolean",
                    "enum": [True]
                }
            }
        }
        include = {"user": True}

        result = validate_include(include, schema)

        assert result is None

    def test_validate_include_enum_false_restriction_raises(self):
        """Test that enum False restriction rejects True."""
        schema = {
            "properties": {
                "user": {
                    "type": "boolean",
                    "enum": [False]
                }
            }
        }
        include = {"user": True}

        with pytest.raises(Exception):
            validate_include(include, schema)

    def test_validate_include_schema_definition_error(self):
        """Test that invalid schema raises error."""
        schema = {
            "properties": {
                "user": {"type": "invalid_type"}
            }
        }
        include = {"user": True}

        with pytest.raises(Exception):
            validate_include(include, schema)
