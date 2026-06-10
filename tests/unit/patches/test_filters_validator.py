import pytest

from app.patches.validators.filters import validate_filters


class TestFiltersValidator:
    """Test filter parameter validation."""

    def test_validate_filters_valid_dict(self):
        """Test validation of valid filter dict."""
        schema = {
            "properties": {
                "id": {
                    "type": "object",
                    "properties": {
                        "eq": {"type": "integer"}
                    }
                }
            }
        }
        filters = {"id": {"eq": 123}}

        result = validate_filters(filters, schema)

        assert result is None

    def test_validate_filters_shorthand_value(self):
        """Test validation of shorthand scalar filter."""
        schema = {
            "properties": {
                "id": {"type": "integer"}
            }
        }
        filters = {"id": 123}

        result = validate_filters(filters, schema)

        assert result is None

    def test_validate_filters_nested_filter(self):
        """Test validation of nested filter."""
        schema = {
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string"}
                    }
                }
            }
        }
        filters = {"user": {"username": "test"}}

        result = validate_filters(filters, schema)

        assert result is None

    def test_validate_filters_oneof_condition_object(self):
        """Test validation of oneOf with condition object."""
        schema = {
            "properties": {
                "id": {
                    "oneOf": [
                        {"type": "integer"},
                        {
                            "type": "object",
                            "properties": {
                                "eq": {"type": "integer"}
                            }
                        }
                    ]
                }
            }
        }
        filters = {"id": {"eq": 123}}

        result = validate_filters(filters, schema)

        assert result is None

    def test_validate_filters_oneof_shorthand_value(self):
        """Test validation of oneOf with shorthand value."""
        schema = {
            "properties": {
                "id": {
                    "oneOf": [
                        {"type": "integer"},
                        {
                            "type": "object",
                            "properties": {
                                "eq": {"type": "integer"}
                            }
                        }
                    ]
                }
            }
        }
        filters = {"id": 123}

        result = validate_filters(filters, schema)

        assert result is None

    def test_validate_filters_unknown_field_raises(self):
        """Test that unknown fields raise error."""
        schema = {
            "properties": {
                "id": {"type": "integer"}
            }
        }
        filters = {"unknown": 123}

        with pytest.raises(Exception):
            validate_filters(filters, schema)

    def test_validate_filters_expected_dict_raises(self):
        """Test that non-dict filter raises error."""
        schema = {
            "properties": {
                "id": {"type": "integer"}
            }
        }
        filters = "not_a_dict"

        with pytest.raises(Exception):
            validate_filters(filters, schema)

    def test_validate_filters_expected_nested_filter_raises(self):
        """Test that non-dict nested filter raises error."""
        schema = {
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"}
                    }
                }
            }
        }
        filters = {"user": "not_a_dict"}

        with pytest.raises(Exception):
            validate_filters(filters, schema)

    def test_validate_filters_expected_array_raises(self):
        """Test that non-array raises error for array type."""
        schema = {
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
        filters = {"tags": "not_an_array"}

        with pytest.raises(Exception):
            validate_filters(filters, schema)

    def test_validate_filters_array_items_validation(self):
        """Test that array items are validated."""
        schema = {
            "properties": {
                "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
        filters = {"tags": ["tag1", "tag2", "tag3"]}

        result = validate_filters(filters, schema)

        assert result is None

    def test_validate_filters_string_format_date_time(self):
        """Test validation of date-time format."""
        schema = {
            "properties": {
                "created_at": {
                    "type": "string",
                    "format": "date-time"
                }
            }
        }
        filters = {"created_at": "2024-01-01T00:00:00+00:00"}

        result = validate_filters(filters, schema)

        assert result is None

    def test_validate_filters_string_format_date_time_invalid_raises(self):
        """Test that invalid date-time format raises error."""
        schema = {
            "properties": {
                "created_at": {
                    "type": "string",
                    "format": "date-time"
                }
            }
        }
        filters = {"created_at": "not-a-date"}

        with pytest.raises(Exception):
            validate_filters(filters, schema)

    def test_validate_filters_integer_type(self):
        """Test validation of integer type."""
        schema = {
            "properties": {
                "id": {"type": "integer"}
            }
        }
        filters = {"id": 123}

        result = validate_filters(filters, schema)

        assert result is None

    def test_validate_filters_integer_type_raises_for_float(self):
        """Test that float raises error for integer type."""
        schema = {
            "properties": {
                "id": {"type": "integer"}
            }
        }
        filters = {"id": 3.14}

        with pytest.raises(Exception):
            validate_filters(filters, schema)

    def test_validate_filters_number_type(self):
        """Test validation of number type (int or float)."""
        schema = {
            "properties": {
                "value": {"type": "number"}
            }
        }
        filters = {"value": 3.14}

        result = validate_filters(filters, schema)

        assert result is None

    def test_validate_filters_boolean_type(self):
        """Test validation of boolean type."""
        schema = {
            "properties": {
                "visible": {"type": "boolean"}
            }
        }
        filters = {"visible": True}

        result = validate_filters(filters, schema)

        assert result is None

    def test_validate_filters_complex_filter(self):
        """Test validation of complex filter with multiple conditions."""
        schema = {
            "properties": {
                "id": {"type": "integer"},
                "user": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string"},
                        "profile": {
                            "type": "object",
                            "properties": {
                                "osu_id": {"type": "integer"}
                            }
                        }
                    }
                },
                "created_at": {
                    "type": "string",
                    "format": "date-time"
                }
            }
        }
        filters = {
            "id": 123,
            "user": {
                "username": "test",
                "profile": {
                    "osu_id": 456
                }
            },
            "created_at": "2024-01-01T00:00:00+00:00"
        }

        result = validate_filters(filters, schema)

        assert result is None

    def test_validate_filters_null_value(self):
        """Test validation of null value."""
        schema = {
            "properties": {
                "deleted_at": {"type": "null"}
            }
        }
        filters = {"deleted_at": None}

        result = validate_filters(filters, schema)

        assert result is None

    def test_validate_filters_invalid_filter_schema_definition_raises(self):
        """Test that invalid schema raises error."""
        schema = {
            "properties": {
                "id": {"type": "invalid_type"}
            }
        }
        filters = {"id": 123}

        with pytest.raises(Exception):
            validate_filters(filters, schema)

    def test_validate_filters_with_path_tracking(self):
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
        filters = {"user": {"profile": {"settings": True}}}

        result = validate_filters(filters, schema)

        assert result is None

    def test_validate_filters_oneof_no_match_raises(self):
        """Test that oneOf with no matching branch raises error."""
        schema = {
            "properties": {
                "id": {
                    "oneOf": [
                        {"type": "string"},
                        {"type": "integer"}
                    ]
                }
            }
        }
        filters = {"id": []}  # List doesn't match either branch

        with pytest.raises(Exception):
            validate_filters(filters, schema)
