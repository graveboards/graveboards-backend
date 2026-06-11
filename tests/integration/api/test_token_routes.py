import pytest

from jwt.exceptions import ExpiredSignatureError
from app.config import FRONTEND_BASE_URL, JWT_SECRET_KEY, JWT_ALGORITHM
import jwt
from datetime import datetime, timedelta, timezone


class TestTokenEndpoint:
    """Integration tests for /api/v1/token endpoint (GET only via minimal TestClient)."""

    @pytest.mark.integration
    def test_token_get_valid_token(self, TestClient):
        """Test token GET with valid token."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "123",
            "iss": FRONTEND_BASE_URL,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=30)).timestamp())
        }
        valid_token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        response = TestClient.get(
            "/api/v1/token",
            params={"token": valid_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["sub"] == 123
        assert data["iss"] == FRONTEND_BASE_URL

    @pytest.mark.integration
    def test_token_get_invalid_token(self, TestClient):
        """Test token GET with invalid token."""
        response = TestClient.get(
            "/api/v1/token",
            params={"token": "invalid.token.here"}
        )
        
        assert response.status_code == 400
        assert "Invalid or expired JWT" in response.json()["detail"]

    @pytest.mark.integration
    def test_token_get_expired_token(self, TestClient):
        """Test token GET with expired token."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "123",
            "iss": FRONTEND_BASE_URL,
            "iat": int((now - timedelta(days=31)).timestamp()),
            "exp": int((now - timedelta(days=1)).timestamp())
        }
        expired_token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        response = TestClient.get(
            "/api/v1/token",
            params={"token": expired_token}
        )
        
        assert response.status_code == 400
        assert "Invalid or expired JWT" in response.json()["detail"]

    @pytest.mark.integration
    def test_token_get_wrong_issuer(self, TestClient):
        """Test token GET with wrong issuer."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "123",
            "iss": "https://wrong-frontend.com",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=30)).timestamp())
        }
        wrong_issuer_token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        response = TestClient.get(
            "/api/v1/token",
            params={"token": wrong_issuer_token}
        )
        
        assert response.status_code == 400
        assert "Invalid or expired JWT" in response.json()["detail"]

    @pytest.mark.integration
    def test_token_get_missing_token(self, TestClient):
        """Test token GET with missing token parameter."""
        response = TestClient.get(
            "/api/v1/token"
        )
        
        assert response.status_code == 400
        assert "missing" in response.json()["detail"].lower()

    @pytest.mark.integration
    def test_token_get_string_subject(self, TestClient):
        """Test token GET with string subject (should fail validation)."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "not-a-number",
            "iss": FRONTEND_BASE_URL,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=30)).timestamp())
        }
        string_subject_token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        response = TestClient.get(
            "/api/v1/token",
            params={"token": string_subject_token}
        )
        
        assert response.status_code == 400
        assert "Invalid or expired JWT" in response.json()["detail"]
