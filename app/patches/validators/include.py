from app.exceptions import DeepObjectValidationError


def validate_include(
    include: dict,
    schema: dict,
    path: list[str] = None,
):
    """Recursively validate deep-object include structures.

    Enforces:
        - Only declared relationships may be included
        - Boolean vs nested-object constraints
        - oneOf schema resolution for conditional includes
        - Prevention of forbidden recursive relationships

    Args:
        include:
            Nested include dictionary from query parameters.
        schema:
            OpenAPI schema describing allowed structure.
        path:
            Internal recursion path (used for error reporting).

    Raises:
        DeepObjectValidationError:
            On invalid structure or value.
    """
    if path is None:
        path = []

    properties = schema.get("properties", schema)

    for key, value in include.items():
        current_path = path + [key]

        if key not in properties:
            raise DeepObjectValidationError(current_path, "Unknown include field")

        prop = properties[key]
        prop_type = prop.get("type")

        if prop_type == "boolean":
            if (enum := prop.get("enum")) is not None and value not in enum:
                # Catch first for better error clarity in the case of the user providing True or a nested include
                raise DeepObjectValidationError(current_path, "This relationship cannot be included (recursive include is forbidden)")

            if not isinstance(value, bool):
                raise DeepObjectValidationError(current_path, "Expected boolean (true or false)")
        elif "oneOf" in prop:
            obj_branch = None
            bool_branch = None

            for branch in prop["oneOf"]:
                t = branch.get("type")

                if t == "object":
                    obj_branch = branch
                elif t == "boolean":
                    bool_branch = branch

            if isinstance(value, dict):
                if obj_branch is None:
                    raise DeepObjectValidationError(current_path, "Nested includes are not allowed here")

                validate_include(value, obj_branch, current_path)
            elif isinstance(value, bool):
                if bool_branch is None:
                    raise DeepObjectValidationError(current_path, "Boolean value not allowed here")

                enum = bool_branch.get("enum")

                if enum is not None and value not in enum:
                    raise DeepObjectValidationError(current_path, f"This relationship cannot be {"included" if value else "excluded"}")
            else:
                raise DeepObjectValidationError(
                    current_path,
                    "Expected boolean or object"
                )
        elif prop_type == "object":
            if not isinstance(value, dict):
                raise DeepObjectValidationError(current_path, "Expected nested include object")

            validate_include(value, prop, current_path)
        else:
            raise DeepObjectValidationError(current_path, "Invalid include schema definition")
