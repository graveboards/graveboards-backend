import os

from connexion.lifecycle import ConnexionRequest
from connexion.validators import ParameterValidator

from app.exceptions import ArrayValidationError, DeepObjectValidationError, bad_request_factory
from app.spec import get_include_schema
from app.config import API_BASE_PATH


class ParameterValidatorPatched(ParameterValidator):
    """Extended parameter validator with domain-specific logic.

    Adds:
        - Structured validation for `sorting`
        - Deep-object validation for `include`
        - Request-scope tracking for context-aware validation
        - Custom error translation into HTTP 400 responses

    Addresses Connexion limitations around complex query schemas.
    """
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
        """Validate query parameters with custom include/sorting logic.

        Special handling:
            - `sorting`: Field/order validation against schema enums.
            - `include`: Recursive deep-object validation against dynamically resolved
            include schemas.

            - `/search: include validation is deferred due to schema ambiguity.

        Args:
            param:
                Parameter schema definition.
            request:
                Incoming Connexion request.

        Returns:
            Validated and possibly transformed parameter value.

        Raises:
            HTTPException:
                On validation failure.
        """
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

                resolved_schema = get_include_schema(schema_name=param["schema"]["title"])  # F**k Connexion
                return validate_include(value, resolved_schema)
            except DeepObjectValidationError as e:
                raise bad_request_factory(e)

        return self.validate_parameter("query", value, param, param_name=param_name)

    def validate(self, scope: dict):
        """Validate request scope while tracking context.

        Temporarily stores request scope to allow context-aware validation (e.g.,
        route-specific include behavior).

        Args:
            scope:
                ASGI request scope dictionary.
        """
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
    """Validate structured sorting directives.

    Ensures each sorting entry:
        - Contains a valid `field`
        - Uses an allowed `order` (default: ``asc``/``desc``)
        - Does not include unexpected keys

    Args:
        sorting:
            List of sorting dictionaries.
        schema:
            OpenAPI schema defining allowed fields and orders.

    Raises:
        ArrayValidationError:
            If any entry fails validation.
    """
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
            raise DeepObjectValidationError(
                path + [key],
                "Unknown include field"
            )

        prop = properties[key]
        prop_type = prop.get("type")

        if prop_type == "boolean":
            if (enum := prop.get("enum")) is not None and value not in enum:
                # Catch first for better error clarity in the case of the user providing True or a nested include
                raise DeepObjectValidationError(
                    path + [key],
                    "This relationship cannot be included (recursive include is forbidden)"
                )

            if not isinstance(value, bool):
                raise DeepObjectValidationError(
                    current_path,
                    "Expected boolean (true or false)"
                )
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
                    raise DeepObjectValidationError(
                        current_path,
                        "Nested includes are not allowed here"
                    )

                validate_include(value, obj_branch, current_path)
            elif isinstance(value, bool):
                if bool_branch is None:
                    raise DeepObjectValidationError(
                        current_path,
                        "Boolean value not allowed here"
                    )

                enum = bool_branch.get("enum")

                if enum is not None and value not in enum:
                    raise DeepObjectValidationError(
                        current_path,
                        f"This relationship cannot be {"included" if value else "excluded"}"
                    )
            else:
                raise DeepObjectValidationError(
                    current_path,
                    "Expected boolean or object"
                )
        elif prop_type == "object":
            if not isinstance(value, dict):
                raise DeepObjectValidationError(
                    current_path,
                    "Expected nested include object"
                )

            validate_include(value, prop, current_path)
        else:
            raise DeepObjectValidationError(
                current_path,
                "Invalid include schema definition"
            )
