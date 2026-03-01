from datetime import datetime
from typing import Any

from app.exceptions import DeepObjectValidationError


def validate_filters(filters: dict, schema: dict, path: list[str] = None):
    """Recursively validate a deep-object filter structure.

    Supports both canonical condition objects and shorthand scalar filters.

    Handles:
        - OneOf schemas (condition object vs scalar value)
        - Shorthand scalar (implicitly treated as equality)
        - Nested filter objects
        - Condition object key validation (eq, neq, in, regex, etc.)

    Args:
        filters:
            Nested filter dictionary from query parameters.
        schema:
            OpenAPI schema fragment describing allowed filter structure.
        path:
            Internal recursion path (used for error reporting).

    Raises:
        DeepObjectValidationError:
            If any filter does not conform to the schema definition, including unknown
            fields, type mismatches, invalid nested structures, or format violations.
    """
    if path is None:
        path = []

    if not isinstance(filters, dict):
        raise DeepObjectValidationError(path, "Expected a dict for filter object")

    properties = schema.get("properties", {})

    for key, value in filters.items():
        current_path = path + [key]

        if key not in properties:
            raise DeepObjectValidationError(current_path, "Unknown filter field")

        prop_schema = properties[key]

        if "oneOf" in prop_schema:
            matched = False
            last_error = None

            for branch in prop_schema["oneOf"]:
                try:
                    branch_type = branch.get("type")

                    if branch_type == "object":
                        if not isinstance(value, dict):
                            continue

                        validate_filters(value, branch, current_path)
                        matched = True
                        break
                    else:
                        if isinstance(value, dict):
                            continue

                        validate_value(value, branch, current_path)
                        matched = True
                        break
                except DeepObjectValidationError as e:
                    last_error = e

            if not matched:
                raise last_error or DeepObjectValidationError(current_path, "Value does not match any allowed condition schema")

            continue

        validate_value(value, prop_schema, current_path)


def validate_value(value: Any, schema: dict, path: list[str]) -> None:
    """Validate a value against an OpenAPI schema definition.

    Supports validation of:
        - Nested objects (recursively validated)
        - Arrays (with per-item validation)
        - Primitive types (string, integer, number, boolean)
        - Format constraints (e.g., ISO 8601 date-time strings)

    Args:
        value:
            Value to validate.
        schema:
            OpenAPI schema fragment describing the expected structure.
        path:
            Current recursive path within the filter structure, used for precise
            error reporting.

    Raises:
        DeepObjectValidationError:
            If the value does not conform to the schema definition, including type
            mismatches or format violations.
    """
    prop_type = schema.get("type")
    prop_format = schema.get("format")

    match prop_type:
        case "object":
            if not isinstance(value, dict):
                raise DeepObjectValidationError(path, "Expected nested filter object")

            validate_filters(value, schema, path)
        case "array":
            if not isinstance(value, list):
                raise DeepObjectValidationError(path, f"Expected array, got {type(value).__name__}")

            items_schema = schema.get("items", {})

            for i, item in enumerate(value):
                validate_value(item, items_schema, path + [str(i)])
        case "string":
            if not isinstance(value, str):
                raise DeepObjectValidationError(path, f"Expected string, got {type(value).__name__}")

            if prop_format == "date-time":
                try:
                    datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    raise DeepObjectValidationError(path, f"Expected ISO 8601 date-time string, got '{value}'")
        case "integer":
            if not isinstance(value, int):
                raise DeepObjectValidationError(path, f"Expected integer, got {type(value).__name__}")
        case "number":
            if not isinstance(value, (int, float)):
                raise DeepObjectValidationError(path, f"Expected number, got {type(value).__name__}")
        case "boolean":
            if not isinstance(value, bool):
                raise DeepObjectValidationError(path, f"Expected boolean, got {type(value).__name__}")
        case _:
            raise DeepObjectValidationError(path, "Invalid filter schema definition")

