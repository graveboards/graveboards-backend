import json
import re
from datetime import datetime

from connexion.uri_parsing import OpenAPIURIParser
from connexion.utils import coerce_type, TypeValidationError

from app.logging import get_logger

affirmative_literals = {"true", "t", "yes", "y"}
negative_literals = {"false", "f", "no", "n"}
logger = get_logger(__name__)


class OpenAPIURIParserPatched(OpenAPIURIParser):
    """Extended OpenAPI URI parser with custom coercion logic.

    Enhancements:
        - Custom parsing for deepObject `include` parameters
        - JSON-based coercion for `sorting`
        - Improved handling of array-style query parameters
        - Preserve arrays with repeated values in deepObject parameters.

    Designed to support complex filtering, nested includes, and structured query
    parameters not natively handled by Connexion.
    """

    def _make_deep_object(self, k, v):
        """Patched to preserve repeated values for deepObject arrays."""
        if not isinstance(v, list):
            v = [v]

        root_key = None
        if k in self.param_schemas.keys():
            root_key = k
            is_deep = False
        else:
            for key in self.param_schemas.keys():
                if k.startswith(key) and "[" in k:
                    root_key = key
            if not root_key:
                root_key = k.split("[", 1)[0]
            is_deep = self._is_deep_object_style_param(root_key)

        if not is_deep:
            return root_key, v if len(v) > 1 else v[0], False

        key_path = re.findall(r"\[([^\[\]]*)\]", k)
        root = prev = node = {}
        for key_part in key_path:
            node[key_part] = {}
            prev = node
            node = node[key_part]

        schema = self.param_schemas.get(root_key, {})
        for kp in key_path[:-1]:
            while "oneOf" in schema:
                # Pick first object branch
                schema = next((b for b in schema["oneOf"] if b.get("type") == "object"), schema["oneOf"][0])

            schema = schema.get("properties", {}).get(kp, {})

        last_key = key_path[-1]

        while "oneOf" in schema:
            schema = next((b for b in schema["oneOf"] if b.get("type") == "object"), schema["oneOf"][0])

        last_schema = schema.get("properties", {}).get(last_key, {})

        if not last_schema:
            logger.warning("no schema found for deepObject leaf %s.%s", root_key, last_key)

        # Preserve list only if leaf type is array
        if last_schema.get("type") == "array":
            if (
                k.startswith("filters") and
                isinstance(v, list) and
                len(v) == 1 and
                isinstance(v[0], str)
            ):
                # Support non-exploded forms
                v = v[0].split(",")

            prev[last_key] = v
        else:
            prev[last_key] = v if isinstance(v, list) else [v]
            if isinstance(prev[last_key], list) and len(prev[last_key]) == 1:
                prev[last_key] = prev[last_key][0]

        return root_key, [root], True

    def resolve_params(self, params, _in):
        """Resolve and coerce incoming request parameters.

        Applies schema-based coercion for standard parameters (copied from connexion),
        and special handling for custom parameters.

        Args:
            params:
                Raw parameter dictionary from the request.
            _in:
                Parameter location ("query", "path", etc.).

        Returns:
            Dictionary of resolved and coerced parameters.
        """
        resolved_param = {}
        for k, values in params.items():
            param_defn = self.param_defns.get(k)
            param_schema = self.param_schemas.get(k)

            if not (param_defn or param_schema):
                resolved_param[k] = values
                continue

            if _in == "path":
                values = [values]

            if param_schema and param_schema["type"] == "array":
                if k == "sorting":
                    resolved_param[k] = values
                else:
                    values = self._resolve_param_duplicates(values, param_defn, _in)
                    resolved_param[k] = self._split(values, param_defn, _in)
            else:
                resolved_param[k] = values

            if k == "include":
                try:
                    resolved_param[k] = self.coerce_include(param_defn, resolved_param[k], "parameter", k)
                except TypeValidationError:
                    pass
            elif k == "sorting":
                try:
                    resolved_param[k] = self.coerce_sorting(param_defn, resolved_param[k], "parameter", k)
                except TypeValidationError:
                    pass
            elif k == "filters":
                try:
                    resolved_param[k] = self.coerce_filters(param_defn, resolved_param[k], "parameter", k)
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
        """Recursively coerce deep-object include parameters.

        Supports:
            - Boolean string casting (``"true"``/``"false"``)
            - oneOf schema branch resolution
            - Recursive object and array casting

        Args:
            param:
                Parameter definition or schema.
            value:
                Raw include value.
            parameter_type:
                Location context (unused but required).
            parameter_name:
                Parameter name (optional).

        Returns:
            Coerced include structure matching schema shape.
        """
        param_schema = param.get("schema", param)

        def resolve_oneof(schema, data):
            if not isinstance(schema, dict):
                return schema

            if "oneOf" not in schema:
                return schema

            for branch in schema["oneOf"]:
                branch_type = branch.get("type")

                if branch_type == "object" and isinstance(data, dict):
                    return branch

                if branch_type == "array" and isinstance(data, list):
                    return branch

                if branch_type == "boolean" and (
                    isinstance(data, bool) or
                    isinstance(data, str) and
                    data.lower() in affirmative_literals | negative_literals
                ):
                    return branch

            return schema["oneOf"][0]

        def cast(data, schema):
            if isinstance(data, str):
                lower = data.lower()

                if lower in affirmative_literals:
                    return True
                elif lower in negative_literals:
                    return False

            if isinstance(data, dict):
                if isinstance(schema, dict):
                    schema = resolve_oneof(schema, data)
                    properties = schema.get("properties")
                    additional = schema.get("additionalProperties")

                    new_dict = {}

                    for k, v in data.items():
                        if properties and k in properties:
                            new_dict[k] = cast(v, properties[k])
                        elif isinstance(additional, dict):
                            new_dict[k] = cast(v, additional)
                        else:
                            new_dict[k] = cast(v, {})

                    return new_dict

                return {k: cast(v, {}) for k, v in data.items()}

            if isinstance(data, list):
                if isinstance(schema, dict):
                    items_schema = schema.get("items", {})
                else:
                    items_schema = {}

                return [cast(v, items_schema) for v in data]

            return data

        if isinstance(value, list) and len(value) == 1:
            return cast(value[0], param_schema)

        return cast(value, param_schema)

    @staticmethod
    def coerce_sorting(param, value, parameter_type, parameter_name=None):
        """Coerce sorting parameters from JSON-encoded strings.

        Each sorting item is parsed from JSON into a structured dict.

        Args:
            param:
                Parameter definition.
            value:
                List of JSON-encoded sorting items.
            parameter_type:
                Location context (unused but required).
            parameter_name:
                Parameter name (optional).

        Returns:
            List of parsed sorting dictionaries.

        Raises:
            json.JSONDecodeError:
                If any sorting item is invalid JSON.
        """
        if not value:
            return []

        if isinstance(value, str):
            value = [value]

        coerced = []

        for item in value:
            if item is None:
                continue

            try:
                coerced.append(json.loads(item))
            except json.JSONDecodeError:
                raise

        return coerced

    @staticmethod
    def coerce_filters(param, value, parameter_type, parameter_name=None):
        """
        Recursively coerce deep-object filter parameters.

        Supports:
            - Primitive casting for condition values
            - Nested relationship filter objects
            - Preservation of condition mappings

        Args:
            param:
                Parameter definition or schema.
            value:
                Raw filters value.
            parameter_type:
                Location context (unused but required).
            parameter_name:
                Parameter name (optional).

        Returns:
            Coerced filters structure matching schema shape.
        """
        def cast(data):
            if isinstance(data, str):
                lower = data.lower()

                if lower == "true":
                    return True
                if lower == "false":
                    return False

                try:
                    return datetime.fromisoformat(data.replace("Z", "+00:00"))
                except ValueError:
                    pass

                try:
                    if "." in data:
                        return float(data)
                    return int(data)
                except ValueError:
                    return data

            if isinstance(data, dict):
                return {k: cast(v) for k, v in data.items()}

            if isinstance(data, list):
                return [cast(v) for v in data]

            return data

        if isinstance(value, list) and len(value) == 1:
            return cast(value[0])

        return cast(value)
