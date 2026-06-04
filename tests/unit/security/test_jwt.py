import os
from unittest.mock import patch

import pytest

from jwt.exceptions import InvalidTokenError, ExpiredSignatureError


class TestDecodeToken:
    @patch("app.security.jwt.jwt.decode")
    @patch("app.security.jwt.JWT_SECRET_KEY", "test-secret")
    @patch("app.security.jwt.FRONTEND_BASE_URL", "https://example.com")
    def test_decoding_calls_jwt_decode(self, mock_decode):
        from app.security.jwt import decode_token
        mock_decode.return_value = {"sub": "123", "iss": "https://example.com", "iat": 1000, "exp": 2000}
        token = "some.token.here"

        result = decode_token(token)

        mock_decode.assert_called_once_with(
            token,
            key="test-secret",
            algorithms=["HS256"],
            issuer="https://example.com",
            options={"require": ["sub", "iss", "iat", "exp"]}
        )
        assert result == {"sub": "123", "iss": "https://example.com", "iat": 1000, "exp": 2000}

    @patch("app.security.jwt.jwt.decode")
    def test_invalid_token_raises_invalid_token_error(self, mock_decode):
        from app.security.jwt import decode_token
        mock_decode.side_effect = InvalidTokenError("Invalid token")

        with pytest.raises(InvalidTokenError):
            decode_token("invalid.token")

    @patch("app.security.jwt.jwt.decode")
    def test_expired_token_raises_expired_signature_error(self, mock_decode):
        from app.security.jwt import decode_token
        mock_decode.side_effect = ExpiredSignatureError("Token expired")

        with pytest.raises(ExpiredSignatureError):
            decode_token("expired.token")


class TestValidateToken:
    @patch("app.security.jwt.decode_token")
    def test_validates_and_returns_normalized_payload(self, mock_decode):
        from app.security.jwt import validate_token
        mock_decode.return_value = {
            "sub": "123",
            "iss": "https://example.com",
            "iat": 1000,
            "exp": 2000
        }

        result = validate_token("valid.token")

        assert result["sub"] == 123
        assert isinstance(result["sub"], int)
        assert result["iat"] == 1000
        assert result["exp"] == 2000

    @patch("app.security.jwt.decode_token")
    def test_subject_not_digit_raises_invalid_token_error(self, mock_decode):
        from app.security.jwt import validate_token
        mock_decode.return_value = {
            "sub": "not-a-number",
            "iss": "https://example.com",
            "iat": 1000,
            "exp": 2000
        }

        with pytest.raises(Exception, match="Subject is not convertible to an integer"):
            validate_token("invalid-subject.token")

    @patch("app.security.jwt.decode_token")
    def test_float_timestamps_converted_to_int(self, mock_decode):
        from app.security.jwt import validate_token
        mock_decode.return_value = {
            "sub": "123",
            "iss": "https://example.com",
            "iat": 1000.5,
            "exp": 2000.7
        }

        result = validate_token("float-timestamps.token")

        assert result["iat"] == 1000
        assert result["exp"] == 2000
