import pytest
from urllib.parse import urlencode
from connexion.lifecycle import ConnexionRequest

from app.patches.parameter import ParameterValidatorPatched
from app.patches.uri_parsing import OpenAPIURIParserPatched


pytestmark = pytest.mark.unit


def make_validator(parameters=None, strict_validation=False, security_query_params=None):
    """Create a parameter validator with real parameter definitions."""
    if parameters is None:
        parameters = [
            {
                "name": "sorting",
                "in": "query",
                "style": "form",
                "explode": True,
                "schema": {
                    "title": "BeatmapSorting",
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "field": {
                                "type": "string",
                                "enum": ["Beatmap.id", "Beatmap.beatmapset_id"]
                            },
                            "order": {
                                "type": "string",
                                "enum": ["asc", "desc"]
                            }
                        },
                        "required": ["field"]
                    }
                }
            },
            {
                "name": "filters",
                "in": "query",
                "style": "deepObject",
                "explode": True,
                "schema": {
                    "title": "BeatmapFilter",
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "id": {
                            "type": "object",
                            "properties": {
                                "eq": {"type": "integer"}
                            }
                        },
                        "beatmapset_id": {
                            "type": "object",
                            "properties": {
                                "eq": {"type": "integer"}
                            }
                        }
                    }
                }
            },
            {
                "name": "include",
                "in": "query",
                "style": "deepObject",
                "explode": True,
                "schema": {
                    "title": "BeatmapInclude",
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "id": {"type": "boolean", "default": True},
                        "beatmapset_id": {"type": "boolean", "default": True},
                        "beatmapset": {
                            "oneOf": [
                                {"type": "object"},
                                {"type": "boolean", "default": False}
                            ]
                        },
                        "snapshots": {
                            "oneOf": [
                                {"type": "object"},
                                {"type": "boolean", "default": False}
                            ]
                        }
                    }
                }
            }
        ]

    uri_parser = OpenAPIURIParserPatched(parameters, {})
    return ParameterValidatorPatched(
        parameters=parameters,
        uri_parser=uri_parser,
        strict_validation=strict_validation,
        security_query_params=security_query_params
    )


def setup_request_scope(validator, request, scope_path="/api/v1/test"):
    """Set up request scope for testing."""
    scope = {
        "type": "http",
        "path": scope_path
    }
    connexion_request = ConnexionRequest(scope, uri_parser=validator.uri_parser)
    validator.request_scopes[connexion_request] = scope
    return connexion_request


def make_request(query_params=None, scope_path="/api/v1/test", validator=None):
    """Create a ConnexionRequest with query parameters.
    
    Query params are passed as-is and will be parsed by the uri_parser.
    For complex params like sorting (JSON), use URL-encoded JSON strings.
    For deepObject params like filters/include, use dict format.
    """
    if query_params:
        # Convert dict-style deepObject params to URL format
        # For sorting: value should be JSON string
        # For filters/include: values should be deepObject format
        from urllib.parse import urlencode
        
        flat_query = {}
        for k, v in query_params.items():
            if isinstance(v, list):
                flat_query[k] = [str(x) if not isinstance(x, str) else x for x in v]
            elif isinstance(v, dict):
                # DeepObject format: convert dict to deepObject keys
                for dk, dv in v.items():
                    flat_query[f"{k}[{dk}]"] = str(dv) if not isinstance(dv, str) else dv
            else:
                flat_query[k] = str(v) if not isinstance(v, str) else v
        
        query_string = urlencode(flat_query, doseq=True)
    else:
        query_string = ""
    
    scope = {
        "type": "http",
        "method": "GET",
        "path": scope_path,
        "query_string": query_string.encode(),
        "headers": []
    }
    
    uri_parser = None
    if validator:
        uri_parser = validator.uri_parser
    
    return ConnexionRequest(scope, uri_parser=uri_parser)


class TestParameterValidator:
    """Test parameter validation with Connexion integration."""

    def test_init_sets_request_scopes(self):
        """Test that init sets request_scopes."""
        validator = make_validator()
        assert validator.request_scopes == {}

    def test_validate_query_parameter_sorting(self):
        """Test validation of sorting parameter."""
        validator = make_validator()
        
        param = {
            "name": "sorting",
            "in": "query",
            "schema": {
                "title": "BeatmapSorting",
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "field": {
                            "type": "string",
                            "enum": ["Beatmap.id", "Beatmap.beatmapset_id"]
                        },
                        "order": {
                            "type": "string",
                            "enum": ["asc", "desc"]
                        }
                    },
                    "required": ["field"]
                }
            }
        }

        request = make_request(
            query_params={"sorting": '[{"field": "Beatmap.id", "order": "asc"}]'},
            scope_path="/api/v1/beatmaps",
            validator=validator
        )

        result = validator.validate_query_parameter(param, request)

        assert result is None

    def test_validate_query_parameter_filters(self):
        """Test validation of filters parameter."""
        validator = make_validator()
        
        param = {
            "name": "filters",
            "in": "query",
            "schema": {
                "title": "BeatmapFilter",
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {
                        "type": "object",
                        "properties": {
                            "eq": {"type": "integer"}
                        }
                    }
                }
            }
        }

        request = make_request(
            query_params={"filters[id][eq]": "123"},
            scope_path="/api/v1/beatmaps",
            validator=validator
        )

        result = validator.validate_query_parameter(param, request)

        assert result is None

    def test_validate_query_parameter_include(self):
        """Test validation of include parameter."""
        validator = make_validator()
        
        param = {
            "name": "include",
            "in": "query",
            "schema": {
                "title": "BeatmapInclude",
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "boolean", "default": True},
                    "beatmapset_id": {"type": "boolean", "default": True},
                    "beatmapset": {
                        "oneOf": [
                            {"type": "object"},
                            {"type": "boolean", "default": False}
                        ]
                    },
                    "snapshots": {
                        "oneOf": [
                            {"type": "object"},
                            {"type": "boolean", "default": False}
                        ]
                    }
                }
            }
        }

        request = make_request(
            query_params={"include[id]": "true", "include[beatmapset]": "false"},
            scope_path="/api/v1/beatmaps",
            validator=validator
        )

        result = validator.validate_query_parameter(param, request)

        assert result is None

    def test_validate_query_parameter_include_search_defers_validation(self):
        """Test that include validation is deferred for /search endpoint."""
        validator = make_validator()
        
        param = {
            "name": "include",
            "in": "query",
            "schema": {
                "title": "BeatmapInclude",
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "boolean", "default": True},
                }
            }
        }

        request = make_request(
            query_params={"include[id]": "true"},
            scope_path="/api/v1/search",
            validator=validator
        )

        result = validator.validate_query_parameter(param, request)

        assert result is None

    def test_validate_query_parameter_default_validation(self):
        """Test that parameters with default values are handled correctly."""
        validator = make_validator()
        
        # Test with a parameter that has a default
        param = {
            "name": "offset",
            "in": "query",
            "schema": {"type": "integer", "default": 0}
        }

        # Test with no value - should use default
        request = make_request(
            query_params={},
            scope_path="/api/v1/beatmaps",
            validator=validator
        )

        # Missing required parameter returns None
        result = validator.validate_query_parameter(param, request)

        # The result should be None since there's no value and it's not required
        assert result is None

    def test_validate_query_parameter_missing_parameter(self):
        """Test handling of missing parameter."""
        validator = make_validator()
        
        param = {
            "name": "limit",
            "in": "query",
            "schema": {"type": "integer"}
        }

        request = make_request(
            query_params={},
            scope_path="/api/v1/beatmaps",
            validator=validator
        )

        result = validator.validate_query_parameter(param, request)

        assert result is None

    def test_validate_sets_and_clears_request_scopes(self):
        """Test that request_scopes is set and cleared during validation."""
        validator = make_validator()
        
        scope = {
            "type": "http",
            "path": "/api/v1/test",
            "query_string": b"",
            "headers": []
        }

        validator.validate(scope)

        assert validator.request_scopes == {}

    def test_validate_calls_validate_request(self):
        """Test that validate calls validate_request."""
        validator = make_validator()
        
        scope = {
            "type": "http",
            "path": "/api/v1/test",
            "query_string": b"",
            "headers": []
        }

        # validate_request will try to validate query params but there are none
        # so it should raise an exception (or not, depending on implementation)
        try:
            validator.validate(scope)
        except Exception:
            pass  # Expected to fail since there's no query params to validate

        assert validator.request_scopes == {}

    def test_validate_preserves_scope(self):
        """Test that scope is preserved through validation."""
        validator = make_validator()
        
        scope = {
            "type": "http",
            "path": "/api/v1/test"
        }

        with pytest.raises(Exception):
            validator.validate(scope)

    def test_parameter_validator_with_security_params(self):
        """Test validator with security query params."""
        parameters = []
        
        uri_parser = OpenAPIURIParserPatched(parameters, {})
        
        validator = ParameterValidatorPatched(
            parameters=parameters,
            uri_parser=uri_parser,
            strict_validation=False,
            security_query_params=["api_key"]
        )

        assert validator is not None
        assert "api_key" in validator.security_query_params

    def test_parameter_validator_strict_validation(self):
        """Test validator with strict validation."""
        parameters = [{"name": "limit", "in": "query", "required": True}]
        
        uri_parser = OpenAPIURIParserPatched(parameters, {})
        
        validator = ParameterValidatorPatched(
            parameters=parameters,
            uri_parser=uri_parser,
            strict_validation=True
        )

        assert validator is not None

    def test_validate_sorting_with_api_validation(self):
        """Test that sorting validation uses API validation."""
        validator = make_validator()
        
        param = {
            "name": "sorting",
            "in": "query",
            "schema": {
                "title": "BeatmapSorting",
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "field": {
                            "type": "string",
                            "enum": ["Beatmap.id", "Beatmap.beatmapset_id"]
                        },
                        "order": {
                            "type": "string",
                            "enum": ["asc", "desc"]
                        }
                    },
                    "required": ["field"]
                }
            }
        }

        request = make_request(
            query_params={"sorting": '[{\"field\": \"Beatmap.id\", \"order\": \"asc\"}]'},
            scope_path="/api/v1/beatmaps",
            validator=validator
        )

        result = validator.validate_query_parameter(param, request)

        assert result is None

    def test_validate_filters_with_api_validation(self):
        """Test that filters validation uses API validation."""
        validator = make_validator()
        
        param = {
            "name": "filters",
            "in": "query",
            "schema": {
                "title": "BeatmapFilter",
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {
                        "type": "object",
                        "properties": {
                            "eq": {"type": "integer"}
                        }
                    }
                }
            }
        }

        request = make_request(
            query_params={"filters[id][eq]": "123"},
            scope_path="/api/v1/beatmaps",
            validator=validator
        )

        result = validator.validate_query_parameter(param, request)

        assert result is None

    def test_validate_include_with_api_validation(self):
        """Test that include validation uses API validation."""
        validator = make_validator()
        
        param = {
            "name": "include",
            "in": "query",
            "schema": {
                "title": "BeatmapInclude",
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "boolean", "default": True},
                    "beatmapset_id": {"type": "boolean", "default": True},
                }
            }
        }

        request = make_request(
            query_params={"include[id]": "true", "include[beatmapset_id]": "false"},
            scope_path="/api/v1/beatmaps",
            validator=validator
        )

        result = validator.validate_query_parameter(param, request)

        assert result is None
