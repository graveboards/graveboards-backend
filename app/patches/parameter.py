import os
from typing import Any

from connexion.lifecycle import ConnexionRequest
from connexion.validators import ParameterValidator

from app.config import API_BASE_PATH
from app.exceptions import ArrayValidationError, DeepObjectValidationError, bad_request_factory
from app.spec import get_filter_schema, get_include_schema

from .validators import validate_filters, validate_include, validate_sorting


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
        parameters: list[dict],
        uri_parser: Any,
        strict_validation: bool = False,
        security_query_params: list[str] | None = None,
    ):
        super().__init__(
            parameters,
            uri_parser,
            strict_validation=strict_validation,
            security_query_params=security_query_params,
        )
        self.request_scopes: dict[ConnexionRequest, dict] = {}

    def validate_query_parameter(
        self, param: dict[str, Any], request: ConnexionRequest
    ) -> str | None:
        """Validate query parameters with custom include/sorting logic.

        Special handling:
            - `sorting`: Field/order validation against schema enums.
            - `include`: Recursive deep-object validation against dynamically resolved
              include schemas. `/search` validation is deferred due to schema ambiguity.
            - `filters`: Recursive deep-object validation against dynamically resolved
              filter schemas.

        Note:
            Connexion doesn't expose the schema title in the parameter dict, so we
            resolve it manually from ``param["schema"]["title"]``.

        Args:
            param:
                Parameter schema definition.
            request:
                Incoming Connexion request.

        Returns:
            ``None`` if the parameter is valid, otherwise an error message describing
            why validation failed (mirrors the base class' ``validate_parameter``
            contract). Domain-specific failures (`sorting`, `filters`, `include`) are
            raised directly as HTTP exceptions instead of being returned as a string.

        Raises:
            HTTPException:
                On `sorting`, `filters`, or `include` validation failure.
        """
        param_name = param["name"]
        value = request.query_params.get(param_name)

        if param_name == "sorting" and isinstance(value, list):
            try:
                validate_sorting(value, param.get("schema"))
            except ArrayValidationError as e:
                raise bad_request_factory(e) from e

            return None
        elif param_name == "filters" and isinstance(value, dict):
            try:
                resolved_schema = get_filter_schema(schema_name=param["schema"]["title"])
                validate_filters(value, resolved_schema)
            except DeepObjectValidationError as e:
                raise bad_request_factory(e) from e

            return None
        elif param_name == "include" and isinstance(value, dict):
            request_scope = self.request_scopes.get(request, {})
            scope_path = request_scope.get("path", "")
            if scope_path.endswith(os.path.join(API_BASE_PATH.rstrip("/"), "search")):
                # The /search include schema is ambiguous due to multiple possibilities depending on the scope
                # Neither the scope nor the respective include schema can be determined at this point
                # Delegate this validation to be run by the operation function where the context is available
                return None

            try:
                resolved_schema = get_include_schema(schema_name=param["schema"]["title"])
                validate_include(value, resolved_schema)
            except DeepObjectValidationError as e:
                raise bad_request_factory(e) from e

            return None

        return self.validate_parameter("query", value, param, param_name=param_name)

    def validate(self, scope: dict[str, Any]) -> None:
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
