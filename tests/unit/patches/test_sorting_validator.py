import pytest

from app.patches.validators.sorting import validate_sorting


class TestSortingValidator:
    """Test sorting parameter validation."""

    def test_validate_sorting_valid_entry(self):
        """Test validation of valid sorting entry."""
        schema = {
            "items": {
                "properties": {
                    "field": {
                        "enum": ["id", "created_at", "name"]
                    },
                    "order": {
                        "enum": ["asc", "desc"]
                    }
                }
            }
        }
        sorting = [{"field": "id", "order": "asc"}]

        result = validate_sorting(sorting, schema)

        assert result is None

    def test_validate_sorting_missing_order_uses_default(self):
        """Test that missing order defaults to asc."""
        schema = {
            "items": {
                "properties": {
                    "field": {
                        "enum": ["id"]
                    },
                    "order": {
                        "enum": ["asc", "desc"]
                    }
                }
            }
        }
        sorting = [{"field": "id"}]

        result = validate_sorting(sorting, schema)

        assert result is None

    def test_validate_sorting_multiple_entries(self):
        """Test validation of multiple sorting entries."""
        schema = {
            "items": {
                "properties": {
                    "field": {
                        "enum": ["id", "created_at", "name"]
                    },
                    "order": {
                        "enum": ["asc", "desc"]
                    }
                }
            }
        }
        sorting = [
            {"field": "created_at", "order": "desc"},
            {"field": "id", "order": "asc"}
        ]

        result = validate_sorting(sorting, schema)

        assert result is None

    def test_validate_sorting_invalid_field_raises(self):
        """Test that invalid field raises error."""
        schema = {
            "items": {
                "properties": {
                    "field": {
                        "enum": ["id", "created_at"]
                    },
                    "order": {
                        "enum": ["asc", "desc"]
                    }
                }
            }
        }
        sorting = [{"field": "invalid", "order": "asc"}]

        with pytest.raises(Exception):
            validate_sorting(sorting, schema)

    def test_validate_sorting_invalid_order_raises(self):
        """Test that invalid order raises error."""
        schema = {
            "items": {
                "properties": {
                    "field": {
                        "enum": ["id"]
                    },
                    "order": {
                        "enum": ["asc", "desc"]
                    }
                }
            }
        }
        sorting = [{"field": "id", "order": "invalid"}]

        with pytest.raises(Exception):
            validate_sorting(sorting, schema)

    def test_validate_sorting_unknown_order_raises(self):
        """Test that unknown order raises error."""
        schema = {
            "items": {
                "properties": {
                    "field": {
                        "enum": ["id"]
                    },
                    "order": {
                        "enum": ["asc", "desc"]
                    }
                }
            }
        }
        sorting = [{"field": "id", "order": "ascending"}]

        with pytest.raises(Exception):
            validate_sorting(sorting, schema)

    def test_validate_sorting_extra_keys_raises(self):
        """Test that extra keys raise error."""
        schema = {
            "items": {
                "properties": {
                    "field": {
                        "enum": ["id"]
                    },
                    "order": {
                        "enum": ["asc", "desc"]
                    }
                }
            }
        }
        sorting = [{"field": "id", "order": "asc", "extra": "value"}]

        with pytest.raises(Exception):
            validate_sorting(sorting, schema)

    def test_validate_sorting_empty_list(self):
        """Test validation of empty list."""
        schema = {
            "items": {
                "properties": {
                    "field": {"enum": ["id"]},
                    "order": {"enum": ["asc", "desc"]}
                }
            }
        }
        sorting = []

        result = validate_sorting(sorting, schema)

        assert result is None

    def test_validate_sorting_default_order_asc(self):
        """Test that default order is asc."""
        schema = {
            "items": {
                "properties": {
                    "field": {"enum": ["id"]},
                    "order": {"enum": ["asc", "desc"]}
                }
            }
        }
        sorting = [{"field": "id"}]

        # When order is missing, it defaults to "asc"
        result = validate_sorting(sorting, schema)

        assert result is None

    def test_validate_sorting_case_sensitive_enum(self):
        """Test that enum validation is case-sensitive."""
        schema = {
            "items": {
                "properties": {
                    "field": {"enum": ["id"]},
                    "order": {"enum": ["asc", "desc"]}
                }
            }
        }
        sorting = [{"field": "id", "order": "ASC"}]

        with pytest.raises(Exception):
            validate_sorting(sorting, schema)

    def test_validate_sorting_no_field_raises(self):
        """Test that missing field raises error."""
        schema = {
            "items": {
                "properties": {
                    "field": {"enum": ["id"]},
                    "order": {"enum": ["asc", "desc"]}
                }
            }
        }
        sorting = [{"order": "asc"}]

        with pytest.raises(Exception):
            validate_sorting(sorting, schema)

    def test_validate_sorting_field_not_in_enum_raises(self):
        """Test that field not in enum raises error."""
        schema = {
            "items": {
                "properties": {
                    "field": {"enum": ["id", "name"]},
                    "order": {"enum": ["asc", "desc"]}
                }
            }
        }
        sorting = [{"field": "created_at", "order": "asc"}]

        with pytest.raises(Exception):
            validate_sorting(sorting, schema)

    def test_validate_sorting_multiple_extra_keys_raises(self):
        """Test that multiple extra keys raise error."""
        schema = {
            "items": {
                "properties": {
                    "field": {"enum": ["id"]},
                    "order": {"enum": ["asc", "desc"]}
                }
            }
        }
        sorting = [{"field": "id", "order": "asc", "key1": "val1", "key2": "val2"}]

        with pytest.raises(Exception):
            validate_sorting(sorting, schema)

    def test_validate_sorting_null_field_raises(self):
        """Test that null field raises error."""
        schema = {
            "items": {
                "properties": {
                    "field": {"enum": ["id"]},
                    "order": {"enum": ["asc", "desc"]}
                }
            }
        }
        sorting = [{"field": None, "order": "asc"}]

        with pytest.raises(Exception):
            validate_sorting(sorting, schema)

    def test_validate_sorting_empty_field_raises(self):
        """Test that empty field raises error."""
        schema = {
            "items": {
                "properties": {
                    "field": {"enum": ["id"]},
                    "order": {"enum": ["asc", "desc"]}
                }
            }
        }
        sorting = [{"field": "", "order": "asc"}]

        with pytest.raises(Exception):
            validate_sorting(sorting, schema)

    def test_validate_sorting_invalid_index_in_array(self):
        """Test that invalid sorting entry raises with correct index."""
        schema = {
            "items": {
                "properties": {
                    "field": {"enum": ["id"]},
                    "order": {"enum": ["asc", "desc"]}
                }
            }
        }
        sorting = [
            {"field": "valid", "order": "asc"},
            {"field": "invalid", "order": "asc"}
        ]

        with pytest.raises(Exception):
            validate_sorting(sorting, schema)

    def test_validate_sorting_with_schema_no_items(self):
        """Test that schema without items raises error."""
        schema = {"properties": {}}
        sorting = [{"field": "id", "order": "asc"}]

        # Should fail because we can't get allowed fields from schema
        with pytest.raises(Exception):
            validate_sorting(sorting, schema)
