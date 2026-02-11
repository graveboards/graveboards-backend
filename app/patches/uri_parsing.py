from connexion.uri_parsing import OpenAPIURIParser
from connexion.utils import coerce_type, boolean, TypeValidationError

NESTED_INCLUDE_KEY_TITLE_MAPPING = {
    "user_profile": "ProfileInclude",
    "owner_profiles": "ProfileInclude",
    "manager_profiles": "ProfileInclude",
    "beatmap_snapshot": "BeatmapSnapshotInclude",
    "beatmap_snapshots": "BeatmapSnapshotInclude",
    "beatmap_tags": "BeatmapTagInclude",
    "beatmapset_snapshot": "BeatmapsetSnapshotInclude",
    "beatmapset_snapshots": "BeatmapsetSnapshotInclude",
    "beatmapset_tags": "BeatmapsetTagInclude",
    "queue": "QueueInclude"
}


class OpenAPIURIParserPatched(OpenAPIURIParser):
    def resolve_params(self, params, _in):
        resolved_param = {}
        for k, values in params.items():
            param_defn = self.param_defns.get(k)
            param_schema = self.param_schemas.get(k)

            if not (param_defn or param_schema):
                # rely on validation
                resolved_param[k] = values
                continue

            if _in == "path":
                # multiple values in a path is impossible
                values = [values]

            if param_schema and param_schema["type"] == "array":
                # resolve variable re-assignment, handle explode
                values = self._resolve_param_duplicates(values, param_defn, _in)
                # handle array styles
                resolved_param[k] = self._split(values, param_defn, _in)
            else:
                resolved_param[k] = values[-1]

            # Use custom coerce_type specifically for include
            if k == "include":
                try:
                    resolved_param[k] = self.coerce_include(param_defn, resolved_param[k], "parameter", k)
                except TypeValidationError:
                    pass
            else:
                try:
                    resolved_param[k] = coerce_type(param_defn, resolved_param[k], "parameter", k)
                except TypeValidationError:
                    pass

        return resolved_param

    @staticmethod
    def coerce_include(param, value, parameter_type, parameter_name=None):
        param_schema = param.get("schema", param)
        param_type = param_schema.get("type")

        def cast(d, schema):
            if "oneOf" in schema:
                for branch in schema["oneOf"]:
                    branch_type = branch.get("type")

                    if branch_type == "object" and isinstance(d, dict):
                        schema = branch
                        break

                    if branch_type == "boolean" and isinstance(d, str) and d.lower() in ("true", "false"):
                        schema = branch
                        break

            if isinstance(d, dict) and (additional_props := schema.get("additionalProperties")):
                for k, v in d.items():
                    if isinstance(v, dict) and k in NESTED_INCLUDE_KEY_TITLE_MAPPING:
                        title = NESTED_INCLUDE_KEY_TITLE_MAPPING[k]

                        for branch in additional_props["oneOf"]:
                            if branch.get("title") == title:
                                d[k] = cast(v, branch)
                    elif isinstance(v, str) and v.lower() in ("true", "false"):
                        d[k] = boolean(v)
                    else:
                        raise TypeValidationError(param_type, parameter_type, parameter_name)

                return d

            if isinstance(d, dict) and (props := schema.get("properties")):
                for k, v in d.items():
                    if k in props:
                        sub_schema = props[k]
                        d[k] = cast(v, sub_schema)
                    else:
                        d[k] = boolean(v)

                return d

            if schema.get("type") == "boolean":
                try:
                    return boolean(d)
                except ValueError:
                    return value

            # Primitive types
            TYPE_MAP = {"integer": int, "number": float, "boolean": boolean, "object": dict}
            type_func = TYPE_MAP.get(schema.get("type"), lambda x: x)

            try:
                return type_func(d)
            except ValueError:
                raise TypeValidationError(param_type, parameter_type, parameter_name)
            except TypeError:
                return value

        return cast(value, param_schema)
