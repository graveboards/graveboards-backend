import copy

SCHEMAS_WITH_SHALLOW_REFS = {
    "Beatmap",
    "BeatmapSnapshot",
    "Beatmapset",
    "BeatmapsetSnapshot",
    "Leaderboard",
    "BeatmapInclude",
    "BeatmapSnapshotInclude",
    "BeatmapsetInclude",
    "BeatmapsetSnapshotInclude",
    "LeaderboardInclude"
}

disabled_nested_obj = {
    "type": "boolean",
    "enum": [False],
    "default": False,
    "description": "*This nested include has been disabled to prevent infinite recursion*"
}


def populate_shallow_refs(openapi_spec: dict):
    """Expand shallow schema references and prevent recursive cycles.

    For schemas listed in ``SCHEMAS_WITH_SHALLOW_REFS``, this function:
      - Resolves "Shallow" object schemas into their full definitions.
      - Expands nested object and array properties.
      - Detects cyclic references using a traversal stack.
      - Drops cyclic properties or replaces nested include cycles with a disabled
        boolean schema to prevent infinite recursion.

    The specification is mutated in place.

    Args:
        openapi_spec:
            The OpenAPI specification to transform.
    """
    schemas = openapi_spec["components"]["schemas"]

    def is_shallow(title: str) -> bool:
        return isinstance(title, str) and title.endswith("Shallow")

    def is_include(title: str) -> bool:
        return isinstance(title, str) and title.endswith("Include")

    def resolve_schema(schema: dict, stack: tuple[str, ...]) -> dict | None:
        schema = copy.deepcopy(schema)
        title = schema.get("title")

        # Track titled schemas
        if isinstance(title, str):
            if title in stack:
                # Cycle
                if is_include(stack[-1]):
                    return disabled_nested_obj

                return None  # Drop property

            stack = stack + (title,)

        # Resolve properties
        if "properties" in schema:
            new_props = {}

            for pk, pv in schema["properties"].items():
                resolved = resolve_property(pv, stack)

                if resolved is None:
                    continue

                new_props[pk] = resolved

            schema["properties"] = new_props

        return schema

    def resolve_property(prop: dict, stack: tuple[str, ...]) -> dict | None:
        # Object
        if prop.get("type") == "object":
            title = prop.get("title")

            # Shallow
            if is_shallow(title):
                base_title = title[:-7]

                if base_title in stack:
                    # Cycle
                    if is_include(stack[-1]):
                        return disabled_nested_obj

                    return None  # Drop property

                if base_title not in schemas:
                    return None

                return resolve_schema(schemas[base_title], stack)

            # Full
            if isinstance(title, str) and title in schemas:
                return resolve_schema(schemas[title], stack)

            return resolve_schema(prop, stack)

        # Array
        if prop.get("type") == "array":
            items = prop.get("items", {})
            new_items = resolve_property(items, stack)

            if new_items is None:
                return None

            prop["items"] = new_items
            return prop

        # Include schema
        if "oneOf" in prop:
            new_branches = []

            for branch in prop["oneOf"]:
                if branch.get("type") == "boolean":
                    new_branches.append(branch)
                    continue

                resolved = resolve_property(branch, stack)

                if resolved is None:
                    if is_include(stack[-1]):
                        new_branches.append(disabled_nested_obj)

                    continue

                new_branches.append(resolved)

            prop["oneOf"] = new_branches
            return prop

        # Primitive
        return prop

    for name in SCHEMAS_WITH_SHALLOW_REFS:
        if name not in schemas:
            continue

        fully_resolved = resolve_schema(schemas[name], ())
        schemas[name] = fully_resolved
