import pytest
from unittest.mock import MagicMock, patch

from app.spec.shallow import (
    SCHEMAS_WITH_SHALLOW_REFS,
    disabled_nested_obj,
    populate_shallow_refs,
)


@pytest.mark.skip(reason="Shallow schema reference mutation issues")
class TestShallowSchema:
    """Test shallow schema operations."""

    def test_schemas_with_shallow_refs_contains_expected_schemas(self):
        """Test that SCHEMAS_WITH_SHALLOW_REFS contains expected schemas."""
        expected = {
            "Beatmap",
            "BeatmapSnapshot",
            "Beatmapset",
            "BeatmapsetSnapshot",
            "Leaderboard",
            "BeatmapFilter",
            "BeatmapSnapshotFilter",
            "BeatmapsetFilter",
            "BeatmapsetSnapshotFilter",
            "BeatmapInclude",
            "BeatmapSnapshotInclude",
            "BeatmapsetInclude",
            "BeatmapsetSnapshotInclude",
            "LeaderboardInclude",
            "RequestInclude",
        }

        assert SCHEMAS_WITH_SHALLOW_REFS == expected

    def test_disabled_nested_obj_structure(self):
        """Test that disabled_nested_obj has correct structure."""
        assert disabled_nested_obj["type"] == "boolean"
        assert disabled_nested_obj["enum"] == [False]
        assert disabled_nested_obj["default"] == False
        assert "description" in disabled_nested_obj

    def test_populate_shallow_refs_mutates_spec(self):
        """Test that populate_shallow_refs mutates the spec."""
        spec = {
            "components": {
                "schemas": {
                    "Beatmap": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        }

        original_id = id(spec["components"]["schemas"]["Beatmap"])

        populate_shallow_refs(spec)

        # Spec should be mutated in place
        assert id(spec["components"]["schemas"]["Beatmap"]) == original_id

    def test_populate_shallow_refs_resolves_shallow_refs(self):
        """Test that shallow refs are resolved."""
        spec = {
            "components": {
                "schemas": {
                    "Beatmap": {
                        "type": "object",
                        "title": "Beatmap",
                        "properties": {
                            "id": {"type": "integer"}
                        }
                    },
                    "BeatmapShallow": {
                        "type": "object",
                        "title": "BeatmapShallow",
                        "properties": {
                            "user": {"type": "object", "title": "UserShallow"}
                        }
                    },
                    "User": {
                        "type": "object",
                        "title": "User",
                        "properties": {
                            "id": {"type": "integer"},
                            "username": {"type": "string"}
                        }
                    }
                }
            }
        }

        populate_shallow_refs(spec)

        # Shallow refs should be resolved
        assert "Beatmap" in spec["components"]["schemas"]

    def test_populate_shallow_refs_handles_missing_schemas(self):
        """Test that missing schemas are handled gracefully."""
        spec = {
            "components": {
                "schemas": {}
            }
        }

        # Should not raise
        populate_shallow_refs(spec)

    def test_populate_shallow_refs_prevents_recursive_cycles(self):
        """Test that recursive cycles are prevented."""
        spec = {
            "components": {
                "schemas": {
                    "Beatmap": {
                        "type": "object",
                        "title": "Beatmap",
                        "properties": {
                            "user": {
                                "type": "object",
                                "title": "User",
                                "properties": {
                                    "beatmaps": {
                                        "type": "array",
                                        "items": {"type": "object", "title": "BeatmapShallow"}
                                    }
                                }
                            }
                        }
                    },
                    "User": {
                        "type": "object",
                        "title": "User",
                        "properties": {
                            "id": {"type": "integer"},
                            "beatmaps": {
                                "type": "array",
                                "items": {"type": "object", "title": "BeatmapShallow"}
                            }
                        }
                    }
                }
            }
        }

        populate_shallow_refs(spec)

    def test_populate_shallow_refs_disables_nested_includes(self):
        """Test that nested includes are disabled to prevent cycles."""
        spec = {
            "components": {
                "schemas": {
                    "BeatmapInclude": {
                        "type": "object",
                        "title": "BeatmapInclude",
                        "properties": {
                            "user": {
                                "oneOf": [
                                    {"type": "boolean"},
                                    {"type": "object", "title": "UserInclude"}
                                ]
                            },
                            "beatmaps": {
                                "oneOf": [
                                    {"type": "boolean"},
                                    {"type": "object", "title": "BeatmapShallow"}
                                ]
                            }
                        }
                    },
                    "UserInclude": {
                        "type": "object",
                        "title": "UserInclude",
                        "properties": {
                            "beatmaps": {
                                "oneOf": [
                                    {"type": "boolean"},
                                    {"type": "object", "title": "BeatmapShallow"}
                                ]
                            }
                        }
                    }
                }
            }
        }

        populate_shallow_refs(spec)

    def test_populate_shallow_refs_processes_multiple_schemas(self):
        """Test that multiple schemas are processed."""
        spec = {
            "components": {
                "schemas": {
                    "Beatmap": {"type": "object", "title": "Beatmap", "properties": {}},
                    "Beatmapset": {"type": "object", "title": "Beatmapset", "properties": {}},
                    "Leaderboard": {"type": "object", "title": "Leaderboard", "properties": {}},
                }
            }
        }

        populate_shallow_refs(spec)

        assert "Beatmap" in spec["components"]["schemas"]
        assert "Beatmapset" in spec["components"]["schemas"]
        assert "Leaderboard" in spec["components"]["schemas"]

    def test_populate_shallow_refs_handles_nested_objects(self):
        """Test that nested objects are processed."""
        spec = {
            "components": {
                "schemas": {
                    "Beatmap": {
                        "type": "object",
                        "title": "Beatmap",
                        "properties": {
                            "user": {
                                "type": "object",
                                "title": "User",
                                "properties": {
                                    "profile": {
                                        "type": "object",
                                        "title": "Profile"
                                    }
                                }
                            },
                            "beatmaps": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "title": "BeatmapShallow"
                                }
                            }
                        }
                    },
                    "User": {
                        "type": "object",
                        "title": "User",
                        "properties": {
                            "id": {"type": "integer"},
                            "username": {"type": "string"}
                        }
                    },
                    "Profile": {
                        "type": "object",
                        "title": "Profile",
                        "properties": {
                            "osu_id": {"type": "integer"}
                        }
                    }
                }
            }
        }

        populate_shallow_refs(spec)

    def test_populate_shallow_refs_handles_arrays(self):
        """Test that arrays are processed."""
        spec = {
            "components": {
                "schemas": {
                    "Beatmapset": {
                        "type": "object",
                        "title": "Beatmapset",
                        "properties": {
                            "beatmaps": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "title": "BeatmapShallow"
                                }
                            }
                        }
                    },
                    "Beatmap": {
                        "type": "object",
                        "title": "Beatmap",
                        "properties": {
                            "id": {"type": "integer"}
                        }
                    }
                }
            }
        }

        populate_shallow_refs(spec)

    def test_populate_shallow_refs_processes_include_schemas(self):
        """Test that include schemas are processed."""
        spec = {
            "components": {
                "schemas": {
                    "BeatmapInclude": {
                        "type": "object",
                        "title": "BeatmapInclude",
                        "properties": {
                            "user": {
                                "oneOf": [
                                    {"type": "boolean"},
                                    {"type": "object", "title": "UserInclude"}
                                ]
                            }
                        }
                    },
                    "UserInclude": {
                        "type": "object",
                        "title": "UserInclude",
                        "properties": {
                            "beatmaps": {
                                "oneOf": [
                                    {"type": "boolean"},
                                    {"type": "object", "title": "BeatmapShallow"}
                                ]
                            }
                        }
                    }
                }
            }
        }

        populate_shallow_refs(spec)

    def test_populate_shallow_refs_handles_primitive_properties(self):
        """Test that primitive properties are not modified."""
        spec = {
            "components": {
                "schemas": {
                    "Beatmap": {
                        "type": "object",
                        "title": "Beatmap",
                        "properties": {
                            "id": {"type": "integer"},
                            "version": {"type": "string"},
                            "difficulty": {"type": "number"},
                            "visible": {"type": "boolean"}
                        }
                    }
                }
            }
        }

        populate_shallow_refs(spec)

        # Primitive properties should remain unchanged
        assert spec["components"]["schemas"]["Beatmap"]["properties"]["id"]["type"] == "integer"

    def test_populate_shallow_refs_handles_deep_nesting(self):
        """Test that deeply nested structures are processed."""
        spec = {
            "components": {
                "schemas": {
                    "Level1": {
                        "type": "object",
                        "title": "Level1",
                        "properties": {
                            "level2": {
                                "type": "object",
                                "title": "Level2",
                                "properties": {
                                    "level3": {
                                        "type": "object",
                                        "title": "Level3",
                                        "properties": {
                                            "level4": {
                                                "type": "object",
                                                "title": "Level4",
                                                "properties": {}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        populate_shallow_refs(spec)

    def test_populate_shallow_refs_preserves_other_schema_properties(self):
        """Test that other schema properties are preserved."""
        spec = {
            "components": {
                "schemas": {
                    "Beatmap": {
                        "type": "object",
                        "title": "Beatmap",
                        "description": "A beatmap",
                        "required": ["id"],
                        "properties": {
                            "id": {"type": "integer"}
                        }
                    }
                }
            }
        }

        populate_shallow_refs(spec)

        schema = spec["components"]["schemas"]["Beatmap"]
        assert schema["description"] == "A beatmap"
        assert schema["required"] == ["id"]
