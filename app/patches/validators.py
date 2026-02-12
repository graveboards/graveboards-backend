import os

from connexion.lifecycle import ConnexionRequest
from connexion.validators import ParameterValidator

from app.exceptions import ArrayValidationError, DeepObjectValidationError, bad_request_factory
from app.config import API_BASE_PATH


class ParameterValidatorPatched(ParameterValidator):
    def __init__(
        self,
        parameters,
        uri_parser,
        strict_validation=False,
        security_query_params=None
    ):
        super().__init__(parameters, uri_parser, strict_validation=strict_validation, security_query_params=security_query_params)
        self.request_scopes: dict[ConnexionRequest, dict] = {}

    def validate_query_parameter(self, param: dict, request: ConnexionRequest):
        param_name = param["name"]
        value = request.query_params.get(param_name)

        if param_name == "sorting" and value:
            try:
                return validate_sorting(value, param.get("schema"))
            except ArrayValidationError as e:
                raise bad_request_factory(e)
        if param_name == "include" and value:
            try:
                if self.request_scopes[request]["path"] == os.path.join(API_BASE_PATH, "search"):
                    # The /search include schema is ambiguous due to multiple possibilities depending on the scope
                    # Neither the scope nor the respective include schema can be determined at this point
                    # Delegate this validation to be run by the operation function where the context is available
                    return None

                return validate_include(value, param.get("schema"))
            except DeepObjectValidationError as e:
                raise bad_request_factory(e)

        return self.validate_parameter("query", value, param, param_name=param_name)

    def validate(self, scope: dict):
        request = ConnexionRequest(scope, uri_parser=self.uri_parser)

        try:
            self.request_scopes[request] = scope
            self.validate_request(request)
        finally:
            del self.request_scopes[request]


def validate_sorting(
    sorting: list,
    schema: dict
):
    items_schema = schema.get("items", {})
    allowed_fields = set(items_schema.get("properties", {}).get("field", {}).get("enum", []))
    allowed_orders = set(items_schema.get("properties", {}).get("order", {}).get("enum", ["asc", "desc"]))

    for i, item in enumerate(sorting):
        field = item.get("field")

        if not field or field not in allowed_fields:
            raise ArrayValidationError(i, f"Field '{field}' not in {allowed_fields}")

        order = item.get("order", "asc")

        if order not in allowed_orders:
            raise ArrayValidationError(i, f"Order '{order}' not in {allowed_orders}")

        extra_keys = set(item.keys()) - {"field", "order"}

        if extra_keys:
            raise ArrayValidationError(i, f"Unexpected key(s) provided: {extra_keys}")


def validate_include(
    include: dict,
    schema: dict,
    path: list[str] = None,
):
    if path is None:
        path = []

    if "properties" in schema:
        properties = schema["properties"]
    else:
        properties = schema

    for key, value in include.items():
        if key not in properties:
            raise DeepObjectValidationError(
                path + [key],
                "Unknown include field"
            )

        prop = properties[key]

        if prop.get("type") == "boolean":
            if "enum" in prop and value not in prop["enum"]:  # Catch first for better error clarity in the case of the user providing True or a nested include
                raise DeepObjectValidationError(
                    path + [key],
                    "This relationship cannot be included (recursive include is forbidden)"
                )

            if not isinstance(value, bool):
                raise DeepObjectValidationError(
                    path + [key],
                    "Expected boolean (true or false)"
                )
        elif "oneOf" in prop:
            obj_branch = next((b for b in prop["oneOf"] if b.get("type") == "object"), None)
            bool_branch = next((b for b in prop["oneOf"] if b.get("type") == "boolean"), None)

            if isinstance(value, dict):
                if obj_branch is None:
                    raise DeepObjectValidationError(
                        path + [key],
                        "Nested includes are not allowed here"
                    )

                validate_include(value, obj_branch, path + [key])
            elif isinstance(value, bool):
                if bool_branch is None:
                    raise DeepObjectValidationError(
                        path + [key],
                        "Boolean value not allowed here"
                    )

                enum = bool_branch.get("enum")

                if enum is not None and value not in enum:
                    raise DeepObjectValidationError(
                        path + [key],
                        f"This relationship cannot be {"included" if value else "excluded"}"
                    )
            else:
                raise DeepObjectValidationError(
                    path + [key],
                    "Expected boolean or object"
                )
        elif prop.get("type") == "object":
            if isinstance(value, dict):
                validate_include(value, prop, path + [key])
        else:
            raise DeepObjectValidationError(
                path + [key],
                "Invalid include schema definition"
            )
