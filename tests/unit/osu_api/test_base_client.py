import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import time





@pytest.fixture
def mock_redis_client():
    mock_redis = MagicMock()
    mock_redis.hgetall = AsyncMock(return_value=None)
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)
    mock_redis.incr = AsyncMock(return_value=1)
    mock_redis.lock_ctx = MagicMock()
    mock_redis.lock_ctx.__aenter__ = AsyncMock(return_value=None)
    mock_redis.lock_ctx.__aexit__ = AsyncMock(return_value=None)
    return mock_redis


@pytest.mark.asyncio
async def test_initialization(mock_redis_client):
    from app.osu_api.client.base import OsuAPIClientBase
    
    client = OsuAPIClientBase(mock_redis_client)
    
    assert client.rc == mock_redis_client
    assert client._token is None


@pytest.mark.asyncio
async def test_get_token_from_cache(mock_redis_client):
    from app.osu_api.client.base import OsuAPIClientBase
    from app.redis.models import OsuClientOAuthToken
    
    client = OsuAPIClientBase(mock_redis_client)
    current_time = int(time.time())
    future_time = current_time + 3600
    
    mock_token = OsuClientOAuthToken(
        access_token="test_token",
        token_type="Bearer",
        expires_in=3600,
        expires_at=future_time
    )
    client._token = mock_token
    
    token = await client.get_token()
    
    assert token == "test_token"


@pytest.mark.asyncio
async def test_get_token_fetches_from_redis(mock_redis_client):
    from app.osu_api.client.base import OsuAPIClientBase
    from app.redis.models import OsuClientOAuthToken
    
    client = OsuAPIClientBase(mock_redis_client)
    current_time = int(time.time())
    future_time = current_time + 3600
    
    mock_token_dict = {
        "access_token": "redis_token",
        "token_type": "Bearer",
        "expires_in": "3600",
        "expires_at": str(future_time)
    }
    
    mock_redis_client.hgetall.return_value = mock_token_dict
    mock_redis_client.lock_ctx.__aenter__.return_value = None
    
    with patch.object(client, '_oauth') as mock_oauth:
        mock_oauth.fetch_token = AsyncMock(side_effect=Exception("Should not be called"))
        
        with patch('app.osu_api.client.base.OsuClientOAuthToken') as mock_token_class:
            mock_token_obj = MagicMock()
            mock_token_obj.access_token = "redis_token"
            mock_token_obj.expires_at = future_time
            mock_token_obj.deserialize.return_value = mock_token_obj
            mock_token_obj.model_validate.return_value = mock_token_obj
            mock_token_obj.serialize.return_value = mock_token_dict
            
            mock_token_class.deserialize.return_value = mock_token_obj
            mock_token_class.model_validate.return_value = mock_token_obj
            
            token = await client.get_token()
    
    assert token == "redis_token"
    mock_redis_client.hgetall.assert_called_once()


@pytest.mark.asyncio
async def test_get_token_refreshes_when_expired(mock_redis_client):
    from app.osu_api.client.base import OsuAPIClientBase
    from app.redis.models import OsuClientOAuthToken
    
    client = OsuAPIClientBase(mock_redis_client)
    current_time = int(time.time())
    past_time = current_time - 3600
    
    mock_token_dict = {
        "access_token": "expired_token",
        "token_type": "Bearer",
        "expires_in": "3600",
        "expires_at": str(past_time)
    }
    
    mock_redis_client.hgetall.return_value = mock_token_dict
    mock_redis_client.lock_ctx.__aenter__.return_value = None
    
    with patch.object(client, '_oauth') as mock_oauth:
        mock_oauth.fetch_token = AsyncMock(return_value={
            "access_token": "new_token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "expires_at": str(current_time + 3600)
        })
        
        with patch('app.osu_api.client.base.OsuClientOAuthToken') as mock_token_class:
            mock_token_obj = MagicMock()
            mock_token_obj.access_token = "new_token"
            mock_token_obj.expires_at = current_time + 3600
            mock_token_obj.deserialize.return_value = mock_token_obj
            mock_token_obj.model_validate.return_value = mock_token_obj
            mock_token_obj.serialize.return_value = mock_token_dict
            
            mock_token_class.deserialize.return_value = mock_token_obj
            mock_token_class.model_validate.return_value = mock_token_obj
            
            token = await client.get_token()
    
    assert token == "new_token"


@pytest.mark.asyncio
async def test_refresh_token_success(mock_redis_client):
    from app.osu_api.client.base import OsuAPIClientBase
    
    client = OsuAPIClientBase(mock_redis_client)
    current_time = int(time.time())
    
    with patch.object(client, '_oauth') as mock_oauth:
        mock_oauth.fetch_token = AsyncMock(return_value={
            "access_token": "new_token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "expires_at": str(current_time + 3600)
        })
        
        with patch('app.osu_api.client.base.OsuClientOAuthToken') as mock_token_class:
            mock_token_obj = MagicMock()
            mock_token_obj.access_token = "new_token"
            mock_token_obj.expires_at = current_time + 3600
            mock_token_obj.model_validate.return_value = mock_token_obj
            mock_token_obj.serialize.return_value = {
                "access_token": "new_token",
                "token_type": "Bearer",
                "expires_in": "3600",
                "expires_at": str(current_time + 3600)
            }
            
            mock_token_class.model_validate.return_value = mock_token_obj
            
            await client.refresh_token()
    
    assert client._token.access_token == "new_token"
    mock_oauth.fetch_token.assert_called_once()
    mock_redis_client.hset.assert_called_once()





@pytest.mark.asyncio
async def test_get_auth_headers(mock_redis_client):
    from app.osu_api.client.base import OsuAPIClientBase
    
    client = OsuAPIClientBase(mock_redis_client)
    
    headers = await client.get_auth_headers(access_token="test_token")
    
    assert headers == {"Authorization": "Bearer test_token"}


@pytest.mark.asyncio
async def test_get_auth_headers_with_custom_token(mock_redis_client):
    from app.osu_api.client.base import OsuAPIClientBase
    
    client = OsuAPIClientBase(mock_redis_client)
    
    headers = await client.get_auth_headers(access_token="custom_token")
    
    assert headers == {"Authorization": "Bearer custom_token"}


@pytest.mark.asyncio
async def test_format_query_parameters(mock_redis_client):
    from app.osu_api.client.base import OsuAPIClientBase
    
    client = OsuAPIClientBase(mock_redis_client)
    
    params = {"page": 1, "limit": 50, "mode": "osu"}
    query_string = client.format_query_parameters(params)
    
    assert query_string == "?page=1&limit=50&mode=osu"
