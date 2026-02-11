import copy

SCHEMAS_WITH_SHALLOW_REFS = {
    "BeatmapSnapshot",
    "BeatmapsetSnapshot",
    "Leaderboard",
    "BeatmapSnapshotInclude",
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
    schemas = openapi_spec["components"]["schemas"]

    def populate_schema(root_title: str, root_schema: dict):
        for pk, pv in root_schema["properties"].items():
            type_ = pv.get("type")

            if type_ == "object":
                if title := pv.get("title"):
                    if title.endswith("Shallow"):
                        schemas[root_title]["properties"][pk] = make_shallow_schema(title, root_title)
            elif type_ == "array":
                if title := pv["items"].get("title"):
                    if title.endswith("Shallow"):
                        schemas[root_title]["properties"][pk]["items"] = make_shallow_schema(title, root_title)

    def populate_include_schema(root_title: str, root_schema: dict):
        for pk, pv in root_schema["properties"].items():
            if "oneOf" in pv:
                i, obj_branch = next(((i, b) for i, b in enumerate(pv["oneOf"]) if b.get("type") == "object"), (None, None))

                if title := obj_branch.get("title"):
                    if title.endswith("Shallow"):
                        schemas[root_title]["properties"][pk]["oneOf"][i] = make_shallow_include_schema(title, root_title)

    def make_shallow_schema(title: str, root_title: str) -> dict:
        original = schemas[title.rstrip("Shallow")]
        shallow = {**{k: copy.deepcopy(v) for k, v in original.items() if k != "properties"}, **{"properties": {}}}

        for pk, pv in original["properties"].items():
            type_ = pv.get("type")

            if type_ == "object":
                if (title := pv.get("title")) and isinstance(title, str):
                    if title.rstrip("Shallow") == root_title:
                        continue
            elif type_ == "array":
                if (title := pv["items"].get("title")) and isinstance(title, str):
                    if title.rstrip("Shallow") == root_title:
                        continue

            shallow["properties"][pk] = copy.deepcopy(pv)

        return shallow

    def make_shallow_include_schema(title: str, root_title: str) -> dict:
        original = schemas[title.rstrip("Shallow")]
        shallow = {**{k: copy.deepcopy(v) for k, v in original.items() if k != "properties"}, **{"properties": {}}}

        for pk, pv in original["properties"].items():
            if "oneOf" in pv:
                if "oneOf" in pv:
                    obj_branch = next((b for b in pv["oneOf"] if b.get("type") == "object"), None)

                    if title := obj_branch.get("title"):
                        if title.rstrip("Shallow") == root_title:
                            shallow["properties"][pk] = disabled_nested_obj
                            continue

            shallow["properties"][pk] = copy.deepcopy(pv)

        return shallow

    for schema_name, schema in schemas.items():
        if schema_name not in SCHEMAS_WITH_SHALLOW_REFS:
            continue

        if schema_name.endswith("Include"):
            populate_include_schema(schema_name, schema)
        else:
            populate_schema(schema_name, schema)
