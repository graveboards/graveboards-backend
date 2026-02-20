import json
from datetime import datetime

from connexion.uri_parsing import OpenAPIURIParser
from connexion.utils import coerce_type, TypeValidationError


class OpenAPIURIParserPatched(OpenAPIURIParser):
    """Extended OpenAPI URI parser with custom coercion logic.

    Enhancements:
        - Custom parsing for deep-object `include` parameters
        - JSON-based coercion for `sorting`
        - Improved handling of array-style query parameters

    Designed to support complex filtering, nested includes, and structured query
    parameters not natively handled by Connexion.
    """
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
                # rely on validation
                resolved_param[k] = values
                continue

            if _in == "path":
                # multiple values in a path is impossible
                values = [values]

            if param_schema and param_schema["type"] == "array":
                if k == "sorting":
                    resolved_param[k] = values
                else:
                    # resolve variable re-assignment, handle explode
                    values = self._resolve_param_duplicates(values, param_defn, _in)
                    # handle array styles
                    resolved_param[k] = self._split(values, param_defn, _in)
            else:
                resolved_param[k] = values[-1]

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

                if branch_type == "boolean":
                    return branch

            return schema["oneOf"][0]

        def cast(data, schema):
            if isinstance(data, str):
                lower = data.lower()

                if lower == "true":
                    return True

                if lower == "false":
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
        coerced = []

        for item in value:
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

        return cast(value)
