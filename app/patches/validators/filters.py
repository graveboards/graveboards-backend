from datetime import datetime

from app.exceptions import DeepObjectValidationError


def validate_filters(filters: dict, schema: dict, path: list[str] = None):
    """Recursively validate deep-object filter structures.

    Handles:
        - OneOf leaf schemas (Condition object vs raw value)
        - Nested filter objects
        - Leaf condition object key validation (eq, neq, in, regex, etc.)
        - additionalProperties enforcement

    Args:
        filters:
            Nested filter dictionary from query parameters.
        schema:
            OpenAPI schema describing allowed structure.
        path:
            Internal recursion path (used for error reporting).

    Raises:
        DeepObjectValidationError:
            On invalid structure or type mismatch.
    """
    if path is None:
        path = []

    if not isinstance(filters, dict):
        raise DeepObjectValidationError(path, "Expected a dict for filter object")

    properties = schema.get("properties", {})
    additional_props = schema.get("additionalProperties", True)

    for key, value in filters.items():
        current_path = path + [key]

        if key not in properties:
            if not additional_props:
                raise DeepObjectValidationError(current_path, "Unknown filter field")

            continue

        prop_schema = properties[key]

        if "oneOf" in prop_schema:
            matched = False
            last_error = None

            for branch in prop_schema["oneOf"]:
                try:
                    validate_filters({key: value} if branch.get("type") == "object" else value, branch, path)
                    matched = True
                    break
                except DeepObjectValidationError as e:
                    last_error = e

            if not matched:
                raise last_error or DeepObjectValidationError(current_path, "Value does not match any allowed condition schema")

            continue

        prop_type = prop_schema.get("type")
        prop_format = prop_schema.get("format")

        match prop_type:
            case "object":
                if not isinstance(value, dict):
                    raise DeepObjectValidationError(current_path, "Expected nested filter object")

                validate_filters(value, prop_schema, current_path)
            case "array":
                if not isinstance(value, list):
                    raise DeepObjectValidationError(current_path, f"Expected array, got {type(value).__name__}")

                items_schema = prop_schema.get("items", {})

                for i, item in enumerate(value):
                    validate_filters(item, items_schema, current_path + [str(i)])
            case "string":
                if not isinstance(value, str):
                    raise DeepObjectValidationError(current_path, f"Expected string, got {type(value).__name__}")

                if prop_format == "date-time":
                    try:
                        datetime.fromisoformat(value.replace("Z", "+00:00"))
                    except ValueError:
                        raise DeepObjectValidationError(current_path, f"Expected ISO 8601 date-time string, got '{value}'")
            case "integer":
                if not isinstance(value, int):
                    raise DeepObjectValidationError(current_path, f"Expected integer, got {type(value).__name__}")
            case "number":
                if not isinstance(value, (int, float)):
                    raise DeepObjectValidationError(current_path, f"Expected number, got {type(value).__name__}")
            case "boolean":
                if not isinstance(value, bool):
                    raise DeepObjectValidationError(current_path, f"Expected boolean, got {type(value).__name__}")
            case _:
                raise DeepObjectValidationError(current_path, "Invalid filter schema definition")
