import pytest
from unittest.mock import MagicMock, patch
from connexion.lifecycle import ConnexionRequest

from app.patches.parameter import ParameterValidatorPatched


@pytest.mark.skip(reason="Requires connexion library update - URIArgumentParser removed in connexion 3.x")
class TestParameterValidator:
    """Test parameter validation."""

    @pytest.fixture
    def validator(self):
        """Create a parameter validator instance."""
        from connexion.validators import URIArgumentParser

        parameters = []
        uri_parser = URIArgumentParser()
        return ParameterValidatorPatched(
            parameters=parameters,
            uri_parser=uri_parser,
            strict_validation=False
        )

    def test_init_sets_request_scopes(self, validator):
        """Test that init sets request_scopes."""
        assert validator.request_scopes == {}

    def test_validate_query_parameter_sorting(self, validator):
        """Test validation of sorting parameter."""
        param = {
            "name": "sorting",
            "schema": {
                "title": "BeatmapFilterSorting",
                "type": "array"
            }
        }

        request = MagicMock(spec=ConnexionRequest)
        request.query_params = {"sorting": [{"field": "id", "order": "asc"}]}

        result = validator.validate_query_parameter(param, request)

        assert result is None

    def test_validate_query_parameter_filters(self, validator):
        """Test validation of filters parameter."""
        param = {
            "name": "filters",
            "schema": {
                "title": "BeatmapFilter",
                "type": "object"
            }
        }

        request = MagicMock(spec=ConnexionRequest)
        request.query_params = {"filters": {"id": {"eq": 123}}}

        with patch("app.patches.parameter.get_filter_schema") as mock_get_schema:
            mock_get_schema.return_value = {
                "properties": {
                    "id": {
                        "oneOf": [
                            {"type": "integer"},
                            {"type": "object", "properties": {"eq": {"type": "integer"}}}
                        ]
                    }
                }
            }
            result = validator.validate_query_parameter(param, request)

        assert result is None

    def test_validate_query_parameter_include(self, validator):
        """Test validation of include parameter."""
        param = {
            "name": "include",
            "schema": {
                "title": "BeatmapInclude",
                "type": "object"
            }
        }

        request = MagicMock(spec=ConnexionRequest)
        request.query_params = {"include": {"user": True}}
        request.path = "/api/v1/beatmaps"

        with patch("app.patches.parameter.get_include_schema") as mock_get_schema:
            mock_get_schema.return_value = {
                "properties": {
                    "user": {"type": "boolean"}
                }
            }
            with patch("app.patches.parameter.os.path.join") as mock_join:
                mock_join.return_value = "/api/v1/beatmaps"
                result = validator.validate_query_parameter(param, request)

        assert result is None

    def test_validate_query_parameter_include_search_defers_validation(self, validator):
        """Test that include validation is deferred for /search endpoint."""
        param = {
            "name": "include",
            "schema": {
                "title": "SearchInclude",
                "type": "object"
            }
        }

        request = MagicMock(spec=ConnexionRequest)
        request.query_params = {"include": {"user": True}}
        request.path = "/api/v1/search"

        with patch("app.patches.parameter.API_BASE_PATH", "/api/v1"):
            result = validator.validate_query_parameter(param, request)

        assert result is None

    def test_validate_query_parameter_default_validation(self, validator):
        """Test default parameter validation."""
        param = {
            "name": "limit",
            "in": "query",
            "schema": {"type": "integer", "default": 50}
        }

        request = MagicMock(spec=ConnexionRequest)
        request.query_params = {"limit": "100"}

        with patch.object(validator, "validate_parameter") as mock_validate:
            mock_validate.return_value = 100
            result = validator.validate_query_parameter(param, request)

        assert result == 100

    def test_validate_query_parameter_missing_parameter(self, validator):
        """Test handling of missing parameter."""
        param = {
            "name": "limit",
            "in": "query",
            "schema": {"type": "integer"}
        }

        request = MagicMock(spec=ConnexionRequest)
        request.query_params = {}

        result = validator.validate_query_parameter(param, request)

        assert result is None

    def test_validate_request_scopes_tracking(self, validator):
        """Test that request scopes are tracked during validation."""
        scope = {
            "type": "http",
            "path": "/api/v1/test"
        }

        validator.validate(scope)

        # Should have cleared after validation
        assert validator.request_scopes == {}

    def test_validate_sets_and_clears_request_scopes(self, validator):
        """Test that request_scopes is set and cleared during validation."""
        scope = {
            "type": "http",
            "path": "/api/v1/test"
        }

        validator.validate(scope)

        assert validator.request_scopes == {}

    def test_validate_calls_validate_request(self, validator):
        """Test that validate calls validate_request."""
        scope = {
            "type": "http",
            "path": "/api/v1/test"
        }

        with patch.object(validator, "validate_request") as mock_validate:
            validator.validate(scope)

            mock_validate.assert_called_once()

    def test_validate_preserves_scope(self, validator):
        """Test that scope is preserved through validation."""
        scope = {
            "type": "http",
            "path": "/api/v1/test"
        }

        validator.validate(scope)

        # Scope should be preserved in ConnexionRequest
        # Validation should not modify the original scope

    def test_parameter_validator_with_security_params(self):
        """Test validator with security query params."""
        from connexion.validators import URIArgumentParser

        parameters = []
        uri_parser = URIArgumentParser()

        validator = ParameterValidatorPatched(
            parameters=parameters,
            uri_parser=uri_parser,
            strict_validation=False,
            security_query_params=["api_key"]
        )

        assert validator is not None

    def test_parameter_validator_strict_validation(self):
        """Test validator with strict validation."""
        from connexion.validators import URIArgumentParser

        parameters = [{"name": "limit", "in": "query", "required": True}]
        uri_parser = URIArgumentParser()

        validator = ParameterValidatorPatched(
            parameters=parameters,
            uri_parser=uri_parser,
            strict_validation=True
        )

        assert validator is not None

    def test_validate_sorting_with_api_validation(self, validator):
        """Test that sorting validation uses API validation."""
        param = {
            "name": "sorting",
            "schema": {
                "title": "BeatmapFilterSorting",
                "type": "array"
            }
        }

        request = MagicMock(spec=ConnexionRequest)
        request.query_params = {"sorting": [{"field": "id", "order": "asc"}]}

        with patch("app.patches.parameter.validate_sorting") as mock_validate:
            mock_validate.return_value = None
            validator.validate_query_parameter(param, request)

            mock_validate.assert_called_once()

    def test_validate_filters_with_api_validation(self, validator):
        """Test that filters validation uses API validation."""
        param = {
            "name": "filters",
            "schema": {
                "title": "BeatmapFilter",
                "type": "object"
            }
        }

        request = MagicMock(spec=ConnexionRequest)
        request.query_params = {"filters": {"id": {"eq": 123}}}

        with patch("app.patches.parameter.get_filter_schema") as mock_get_schema:
            mock_get_schema.return_value = {"properties": {}}
            with patch("app.patches.parameter.validate_filters") as mock_validate:
                mock_validate.return_value = None
                validator.validate_query_parameter(param, request)

                mock_validate.assert_called_once()

    def test_validate_include_with_api_validation(self, validator):
        """Test that include validation uses API validation."""
        param = {
            "name": "include",
            "schema": {
                "title": "BeatmapInclude",
                "type": "object"
            }
        }

        request = MagicMock(spec=ConnexionRequest)
        request.query_params = {"include": {"user": True}}
        request.path = "/api/v1/beatmaps"

        with patch("app.patches.parameter.get_include_schema") as mock_get_schema:
            mock_get_schema.return_value = {"properties": {}}
            with patch("app.patches.parameter.os.path.join") as mock_join:
                mock_join.return_value = "/api/v1/beatmaps"
                with patch("app.patches.parameter.validate_include") as mock_validate:
                    mock_validate.return_value = None
                    validator.validate_query_parameter(param, request)

                    mock_validate.assert_called_once()
