"""JSON schema validation for fetched fixture data.

Validates fetched data against expected schemas before writing to disk.
Prevents corrupted/invalid data from becoming fixtures.
"""

import json
from pathlib import Path
from typing import Any

from app.logging import get_logger

logger = get_logger(__name__)


SCHEMAS = {
    "beatmap": {
        "required_fields": ["id", "beatmapset_id", "difficulty_rating", "total_length"],
        "type_checks": {
            "id": int,
            "beatmapset_id": int,
            "difficulty_rating": (int, float),
            "total_length": (int, float),
        },
        "unwrap_key": "beatmap",
    },
    "beatmapset": {
        "required_fields": ["id", "title", "artist"],
        "type_checks": {
            "id": int,
            "title": str,
            "artist": str,
        },
        "unwrap_key": "beatmapset",
    },
    "user": {
        "required_fields": ["id", "username", "country_code"],
        "type_checks": {
            "id": int,
            "username": str,
            "country_code": str,
        },
        "unwrap_key": "user",
    },
    "scores": {
        "required_fields": [],
        "type_check": list,
    },
    "beatmap_scores": {
        "required_fields": ["scores"],
        "type_check": dict,
    },
    "beatmap_attributes": {
        "required_fields": ["beatmap_id", "mods", "star_rating"],
        "type_checks": {
            "beatmap_id": int,
            "mods": int,
            "star_rating": (int, float),
        },
    },
}


def validate_data(data: Any, data_type: str) -> tuple[bool, str]:
    """Validate fetched data against the schema for the given type.

    Returns:
        Tuple of (is_valid, error_message)
    """
    schema = SCHEMAS.get(data_type)
    if not schema:
        return True, "No schema defined for this type"

    if "type_check" in schema:
        if not isinstance(data, schema["type_check"]):
            return False, f"Expected type {schema['type_check']}, got {type(data).__name__}"
        return True, ""

    if not isinstance(data, dict):
        return False, f"Expected dict, got {type(data).__name__}"

    # Unwrap osu! API v2 responses (e.g., {"beatmap": {...}} -> {...})
    unwrap_key = schema.get("unwrap_key")
    if unwrap_key and unwrap_key in data and isinstance(data[unwrap_key], dict):
        data = data[unwrap_key]

    for field in schema.get("required_fields", []):
        if field not in data:
            return False, f"Missing required field: {field}"

    for field, expected_type in schema.get("type_checks", {}).items():
        if field in data:
            if not isinstance(data[field], expected_type):
                return (
                    False,
                    f"Field '{field}' expected {expected_type}, got {type(data[field]).__name__}",
                )

    return True, ""


def validate_and_write(filepath: Path, data: Any, data_type: str) -> bool:
    """Validate data and write to file if valid.

    Returns:
        True if data was valid and written, False otherwise
    """
    is_valid, error_msg = validate_data(data, data_type)

    if not is_valid:
        logger.warning(f"Validation failed for {data_type}: {error_msg}")
        logger.warning(f"Skipping write to {filepath}")
        return False

    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to write {filepath}: {e}")
        return False
