"""
Test fixtures for token endpoint testing.
"""
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta

from app.redis import RedisClient
from app.osu_api import OsuAPIClient


def create_mock_oauth(fetch_token_response: dict = None):
    """Create a mock OAuth instance for testing.
    
    Args:
        fetch_token_response: Response to return from fetch_token(). Defaults to
            a valid token response with 1 hour expiry.
    
    Returns:
        MagicMock configured as an OAuth instance.
    """
    mock_oauth = MagicMock()
    mock_oauth.fetch_token = AsyncMock(return_value=fetch_token_response or {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_at": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
    })
    return mock_oauth


def create_mock_osu_api_client(user_data: dict = None):
    """Create a mock OsuAPIClient for testing.
    
    Args:
        user_data: User data to return from get_own_data(). Defaults to
            a valid osu! user with ID 12345678.
    
    Returns:
        MagicMock configured as an OsuAPIClient.
    """
    mock_rc = MagicMock(spec=RedisClient)
    mock_client = MagicMock(spec=OsuAPIClient)
    mock_client.rc = mock_rc
    mock_client.get_own_data = AsyncMock(return_value=user_data or {
        "id": 12345678,
        "username": "test_user",
        "avatar_url": "https://example.com/avatar.png"
    })
    return mock_client


def create_valid_token_payload(user_id: int = 12345678):
    """Create a valid JWT payload for testing.
    
    Args:
        user_id: User ID to use in the payload.
    
    Returns:
        Dictionary with JWT payload including sub, iss, iat, exp.
    """
    from app.security import create_token_payload
    return create_token_payload(user_id)


def create_expired_token_payload(user_id: int = 12345678):
    """Create an expired JWT payload for testing.
    
    Args:
        user_id: User ID to use in the payload.
    
    Returns:
        Dictionary with JWT payload that has already expired.
    """
    from app.security import create_token_payload
    payload = create_token_payload(user_id)
    payload["exp"] = int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp())
    return payload
