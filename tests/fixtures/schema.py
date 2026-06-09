"""
JSON Schema validation for test fixture files.

This module defines schemas and validation functions for osu! API response data.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

try:
    from jsonschema import validate, ValidationError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    ValidationError = Exception


# Beatmap schema
BEATMAP_SCHEMA = {
    "type": "object",
    "required": ["id", "beatmapset_id", "status", "mode", "version"],
    "properties": {
        "id": {"type": "integer", "minimum": 1},
        "beatmapset_id": {"type": "integer", "minimum": 1},
        "status": {"type": "string", "enum": ["ranked", "loved", "qualified", "graveyard", "pending", "approved"]},
        "mode": {"type": "integer", "minimum": 0, "maximum": 3},
        "version": {"type": "string", "minLength": 1},
        "difficulty_rating": {"type": "number", "minimum": 0},
        "playcount": {"type": "integer", "minimum": 0},
        "passcount": {"type": "integer", "minimum": 0},
        "mode_int": {"type": "integer", "minimum": 0, "maximum": 3},
    }
}


# Beatmapset schema
BEATMAPSET_SCHEMA = {
    "type": "object",
    "required": ["id", "title", "artist", "creator", "status"],
    "properties": {
        "id": {"type": "integer", "minimum": 1},
        "title": {"type": "string", "minLength": 1},
        "artist": {"type": "string", "minLength": 1},
        "creator": {"type": "string", "minLength": 1},
        "status": {"type": "string", "enum": ["ranked", "loved", "qualified", "graveyard", "pending", "approved"]},
        "bpm": {"type": "number", "minimum": 0},
        "difficulty_rating": {"type": "number", "minimum": 0},
    }
}


# User schema
USER_SCHEMA = {
    "type": "object",
    "required": ["id", "username", "country_code"],
    "properties": {
        "id": {"type": "integer", "minimum": 1},
        "username": {"type": "string", "minLength": 1},
        "country_code": {"type": "string", "minLength": 2, "maxLength": 2},
        "is_active": {"type": "boolean"},
        "statistics": {
            "type": "object",
            "properties": {
                "pp": {"type": "number", "minimum": 0},
                "play_count": {"type": "integer", "minimum": 0},
            }
        },
    }
}


# Score schema
SCORE_SCHEMA = {
    "type": "object",
    "required": ["id", "user_id", "beatmap_id", "rank", "score", "max_combo", "passed"],
    "properties": {
        "id": {"type": "integer", "minimum": 1},
        "user_id": {"type": "integer", "minimum": 1},
        "beatmap_id": {"type": "integer", "minimum": 1},
        "rank": {"type": "string", "enum": ["SS", "S", "A", "B", "C", "D"]},
        "score": {"type": "integer", "minimum": 0},
        "max_combo": {"type": "integer", "minimum": 0},
        "passed": {"type": "boolean"},
        "accuracy": {"type": "number", "minimum": 0, "maximum": 100},
    }
}


# Beatmap attribute schema
BEATMAP_ATTRIBUTE_SCHEMA = {
    "type": "object",
    "required": ["beatmap_id", "difficulty"],
    "properties": {
        "beatmap_id": {"type": "integer", "minimum": 1},
        "difficulty": {"type": "number", "minimum": 0},
        "aim": {"type": "number", "minimum": 0},
        "speed": {"type": "number", "minimum": 0},
    }
}


# Schema map
SCHEMA_MAP = {
    "beatmaps": BEATMAP_SCHEMA,
    "beatmapsets": BEATMAPSET_SCHEMA,
    "users": USER_SCHEMA,
    "scores": SCORE_SCHEMA,
    "beatmap_attributes": BEATMAP_ATTRIBUTE_SCHEMA,
}


def validate_fixture_file(filepath: Path, category: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """Validate a fixture file against its schema.
    
    Args:
        filepath: Path to the JSON fixture file
        category: Optional category name (if None, inferred from path)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not HAS_JSONSCHEMA:
        return True, None  # Skip validation if jsonschema not available
    
    try:
        with open(filepath) as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return False, f"Failed to parse JSON: {e}"
    
    if category is None:
        category = _infer_category_from_path(filepath)
    
    schema = SCHEMA_MAP.get(category)
    if schema is None:
        return True, None
    
    try:
        if isinstance(data, list):
            for item in data:
                validate(instance=item, schema=schema)
        else:
            validate(instance=data, schema=schema)
        return True, None
    except ValidationError as e:
        return False, f"Schema validation error: {e.message} at path: {list(e.path)}"


def validate_all_fixtures(fixtures_dir: Path) -> Dict[str, list]:
    """Validate all fixture files in a directory.
    
    Args:
        fixtures_dir: Directory containing fixture subdirectories
    
    Returns:
        Dictionary mapping categories to list of (filename, is_valid, error) tuples
    """
    results = {}
    
    for category in SCHEMA_MAP.keys():
        category_dir = fixtures_dir / category
        if not category_dir.exists():
            continue
        
        category_results = []
        for filepath in category_dir.glob("*.json"):
            is_valid, error = validate_fixture_file(filepath, category)
            category_results.append((filepath.name, is_valid, error))
        
        results[category] = category_results
    
    return results


def _infer_category_from_path(filepath: Path) -> Optional[str]:
    """Infer category name from file path."""
    parents = filepath.parent.parts
    for parent in reversed(parents):
        if parent in SCHEMA_MAP:
            return parent
    return None


def validate_fixtures_command(fixtures_path: str = "tests/fixtures/osu"):
    """CLI entry point for fixture validation."""
    fixtures_dir = Path(fixtures_path)
    if not fixtures_dir.exists():
        print(f"Error: Fixtures directory not found: {fixtures_dir}")
        return 1
    
    results = validate_all_fixtures(fixtures_dir)
    
    total_valid = 0
    total_invalid = 0
    
    for category, category_results in results.items():
        print(f"\n{category}:")
        for filename, is_valid, error in category_results:
            status = "✓" if is_valid else "✗"
            print(f"  {status} {filename}")
            if error:
                print(f"      Error: {error}")
                total_invalid += 1
            else:
                total_valid += 1
    
    print(f"\n{'=' * 40}")
    print(f"Total valid: {total_valid}")
    print(f"Total invalid: {total_invalid}")
    
    return 0 if total_invalid == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(validate_fixtures_command())
