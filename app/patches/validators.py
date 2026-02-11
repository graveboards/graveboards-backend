import os

from connexion.lifecycle import ConnexionRequest
from connexion.validators import ParameterValidator

from app.exceptions import IncludeValidationError, bad_request_factory
from app.config import API_BASE_PATH


class ParameterValidatorPatched(ParameterValidator):
    def __init__(
            self,
            parameters,
            uri_parser,
            strict_validation=False,
            security_query_params=None,
    ):
        super().__init__(parameters, uri_parser, strict_validation=strict_validation, security_query_params=security_query_params)
        self.request_scopes: dict[ConnexionRequest, dict] = {}

    def validate_query_parameter(self, param: dict, request: ConnexionRequest):
        param_name = param["name"]
        value = request.query_params.get(param_name)

        if param_name == "include" and value:
            try:
                if self.request_scopes[request]["path"] == os.path.join(API_BASE_PATH, "search"):
                    # The /search include schema is ambiguous due to multiple possibilities depending on the scope
                    # Neither the scope nor the respective include schema can be determined at this point
                    # Delegate this validation to be run by the operation function where the context is available
                    return None

                return validate_include(value, param.get("schema"))
            except IncludeValidationError as e:
                raise bad_request_factory(e)

        return self.validate_parameter("query", value, param, param_name=param_name)

    def validate(self, scope: dict):
        request = ConnexionRequest(scope, uri_parser=self.uri_parser)

        try:
            self.request_scopes[request] = scope
            self.validate_request(request)
        finally:
            del self.request_scopes[request]


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
            raise IncludeValidationError(
                path + [key],
                "Unknown include field"
            )

        prop = properties[key]

        if prop.get("type") == "boolean":
            if "enum" in prop and value not in prop["enum"]:  # Catch first for better error clarity in the case of the user providing True or a nested include
                raise IncludeValidationError(
                    path + [key],
                    "This relationship cannot be included (recursive include is forbidden)"
                )

            if not isinstance(value, bool):
                raise IncludeValidationError(
                    path + [key],
                    "Expected boolean (true or false)"
                )
        elif "oneOf" in prop:
            obj_branch = next((b for b in prop["oneOf"] if b.get("type") == "object"), None)
            bool_branch = next((b for b in prop["oneOf"] if b.get("type") == "boolean"), None)

            if isinstance(value, dict):
                if obj_branch is None:
                    raise IncludeValidationError(
                        path + [key],
                        "Nested includes are not allowed here"
                    )

                validate_include(value, obj_branch, path + [key])
            elif isinstance(value, bool):
                if bool_branch is None:
                    raise IncludeValidationError(
                        path + [key],
                        "Boolean value not allowed here"
                    )

                enum = bool_branch.get("enum")

                if enum is not None and value not in enum:
                    raise IncludeValidationError(
                        path + [key],
                        f"This relationship cannot be {"included" if value else "excluded"}"
                    )
            else:
                raise IncludeValidationError(
                    path + [key],
                    "Expected boolean or object"
                )
        elif prop.get("type") == "object":
            if isinstance(value, dict):
                validate_include(value, prop, path + [key])
        else:
            raise IncludeValidationError(
                path + [key],
                "Invalid include schema definition"
            )
