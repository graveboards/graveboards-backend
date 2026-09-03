import time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


@pytest.fixture
def mock_redis_client() -> MagicMock:
    mock_redis = MagicMock()
    mock_redis.hgetall = AsyncMock(return_value=None)
    mock_redis.hset = AsyncMock(return_value=None)
    mock_redis.expire = AsyncMock(return_value=None)
    mock_redis.incr = AsyncMock(return_value=1)
    mock_redis.delete = AsyncMock(return_value=1)
    mock_redis.lock_ctx = MagicMock()
    mock_redis.lock_ctx.__aenter__ = AsyncMock(return_value=None)
    mock_redis.lock_ctx.__aexit__ = AsyncMock(return_value=None)
    return mock_redis


def _mock_response(
    status_code: int, url: str = "https://osu.ppy.sh/api/v2/users/123"
) -> httpx.Response:
    return httpx.Response(status_code, request=httpx.Request("GET", url))


@pytest.mark.asyncio
async def test_initialization(mock_redis_client: MagicMock) -> None:
    from app.osu_api.client.base import OsuAPIClientBase

    client = OsuAPIClientBase(mock_redis_client)

    assert client.rc == mock_redis_client
    assert client._token is None


@pytest.mark.asyncio
async def test_get_token_from_cache(mock_redis_client: MagicMock) -> None:
    from app.osu_api.client.base import OsuAPIClientBase
    from app.redis_client.models import OsuClientOAuthToken

    client = OsuAPIClientBase(mock_redis_client)
    current_time = int(time.time())
    future_time = current_time + 3600

    mock_token = OsuClientOAuthToken(
        access_token="test_token", token_type="Bearer", expires_in=3600, expires_at=future_time
    )
    client._token = mock_token

    token = await client.get_token()

    assert token == "test_token"


@pytest.mark.asyncio
async def test_get_token_fetches_from_redis(mock_redis_client: MagicMock) -> None:
    from app.osu_api.client.base import OsuAPIClientBase

    client = OsuAPIClientBase(mock_redis_client)
    current_time = int(time.time())
    future_time = current_time + 3600

    mock_token_dict = {
        "access_token": "redis_token",
        "token_type": "Bearer",
        "expires_in": "3600",
        "expires_at": str(future_time),
    }

    mock_redis_client.hgetall.return_value = mock_token_dict
    mock_redis_client.lock_ctx.__aenter__.return_value = None

    with patch.object(client, "_oauth") as mock_oauth:
        mock_oauth.fetch_token = AsyncMock(side_effect=Exception("Should not be called"))

        with patch("app.osu_api.client.base.OsuClientOAuthToken") as mock_token_class:
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
async def test_get_token_refreshes_when_expired(mock_redis_client: MagicMock) -> None:
    from app.osu_api.client.base import OsuAPIClientBase

    client = OsuAPIClientBase(mock_redis_client)
    current_time = int(time.time())
    past_time = current_time - 3600

    mock_token_dict = {
        "access_token": "expired_token",
        "token_type": "Bearer",
        "expires_in": "3600",
        "expires_at": str(past_time),
    }

    mock_redis_client.hgetall.return_value = mock_token_dict
    mock_redis_client.lock_ctx.__aenter__.return_value = None

    with patch.object(client, "_oauth") as mock_oauth:
        mock_oauth.fetch_token = AsyncMock(
            return_value={
                "access_token": "new_token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "expires_at": str(current_time + 3600),
            }
        )

        with patch("app.osu_api.client.base.OsuClientOAuthToken") as mock_token_class:
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
async def test_refresh_token_success(mock_redis_client: MagicMock) -> None:
    from app.osu_api.client.base import OsuAPIClientBase

    client = OsuAPIClientBase(mock_redis_client)
    current_time = int(time.time())

    with patch.object(client, "_oauth") as mock_oauth:
        mock_oauth.fetch_token = AsyncMock(
            return_value={
                "access_token": "new_token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "expires_at": str(current_time + 3600),
            }
        )

        with patch("app.osu_api.client.base.OsuClientOAuthToken") as mock_token_class:
            mock_token_obj = MagicMock()
            mock_token_obj.access_token = "new_token"
            mock_token_obj.expires_at = current_time + 3600
            mock_token_obj.model_validate.return_value = mock_token_obj
            mock_token_obj.serialize.return_value = {
                "access_token": "new_token",
                "token_type": "Bearer",
                "expires_in": "3600",
                "expires_at": str(current_time + 3600),
            }

            mock_token_class.model_validate.return_value = mock_token_obj

            await client.refresh_token()

    assert client._token is not None
    assert client._token.access_token == "new_token"
    mock_oauth.fetch_token.assert_called_once()
    mock_redis_client.hset.assert_called_once()


@pytest.mark.asyncio
async def test_is_rate_limit_response() -> None:
    from app.osu_api.client.base import is_rate_limit_response

    assert is_rate_limit_response({"status": 429, "error_code": 1015})
    assert is_rate_limit_response({"error_name": "rate_limited"})
    assert is_rate_limit_response({"cloudflare_error": True})
    assert not is_rate_limit_response(
        {"access_token": "tok", "token_type": "Bearer", "expires_in": 3600}
    )
    assert not is_rate_limit_response({"error": "invalid_grant"})


@pytest.mark.asyncio
async def test_refresh_token_rate_limited_raises(mock_redis_client: MagicMock) -> None:
    from app.osu_api.client.base import OsuAPIClientBase

    client = OsuAPIClientBase(mock_redis_client)
    cloudflare_body = {
        "status": 429,
        "error_code": 1015,
        "error_name": "rate_limited",
        "cloudflare_error": True,
        "retry_after": 1,
    }

    with patch.object(client, "_oauth") as mock_oauth:
        mock_oauth.fetch_token = AsyncMock(return_value=cloudflare_body)
        with patch("app.osu_api.client.base.asyncio.sleep", AsyncMock()) as mock_sleep:
            with pytest.raises(Exception) as excinfo:
                await client.refresh_token()

    assert type(excinfo.value).__name__ == "RateLimitExceededError"
    assert mock_oauth.fetch_token.await_count == 3
    assert mock_sleep.await_count == 2
    mock_redis_client.hset.assert_not_called()


@pytest.mark.asyncio
async def test_refresh_token_rate_limited_then_succeeds(mock_redis_client: MagicMock) -> None:
    from app.osu_api.client.base import OsuAPIClientBase

    client = OsuAPIClientBase(mock_redis_client)
    current_time = int(time.time())
    cloudflare_body = {"status": 429, "error_code": 1015, "retry_after": 1}
    valid_body = {
        "access_token": "new_token",
        "token_type": "Bearer",
        "expires_in": 3600,
        "expires_at": str(current_time + 3600),
    }

    with patch.object(client, "_oauth") as mock_oauth:
        mock_oauth.fetch_token = AsyncMock(side_effect=[cloudflare_body, valid_body])
        with patch("app.osu_api.client.base.asyncio.sleep", AsyncMock()):
            with patch("app.osu_api.client.base.OsuClientOAuthToken") as mock_token_class:
                mock_token_obj = MagicMock()
                mock_token_obj.access_token = "new_token"
                mock_token_obj.expires_at = current_time + 3600
                mock_token_obj.model_validate.return_value = mock_token_obj
                mock_token_obj.serialize.return_value = {
                    "access_token": "new_token",
                    "token_type": "Bearer",
                    "expires_in": "3600",
                    "expires_at": str(current_time + 3600),
                }
                mock_token_class.model_validate.return_value = mock_token_obj

                await client.refresh_token()

    assert client._token.access_token == "new_token"
    assert mock_oauth.fetch_token.await_count == 2
    mock_redis_client.hset.assert_called_once()


@pytest.mark.asyncio
async def test_refresh_token_unexpected_response_raises(mock_redis_client: MagicMock) -> None:
    from app.osu_api.client.base import OsuAPIClientBase

    client = OsuAPIClientBase(mock_redis_client)

    with patch.object(client, "_oauth") as mock_oauth:
        mock_oauth.fetch_token = AsyncMock(return_value={"unexpected": "payload"})
        with patch("app.osu_api.client.base.asyncio.sleep", AsyncMock()):
            with pytest.raises(RuntimeError, match="unexpected response"):
                await client.refresh_token()

    mock_redis_client.hset.assert_not_called()


@pytest.mark.asyncio
async def test_get_auth_headers(mock_redis_client: MagicMock) -> None:
    from app.osu_api.client.base import OsuAPIClientBase

    client = OsuAPIClientBase(mock_redis_client)

    headers = await client.get_auth_headers(access_token="test_token")

    assert headers == {"Authorization": "Bearer test_token"}


@pytest.mark.asyncio
async def test_get_auth_headers_with_custom_token(mock_redis_client: MagicMock) -> None:
    from app.osu_api.client.base import OsuAPIClientBase

    client = OsuAPIClientBase(mock_redis_client)

    headers = await client.get_auth_headers(access_token="custom_token")

    assert headers == {"Authorization": "Bearer custom_token"}


@pytest.mark.asyncio
async def test_format_query_parameters(mock_redis_client: MagicMock) -> None:
    from app.osu_api.client.base import OsuAPIClientBase

    client = OsuAPIClientBase(mock_redis_client)

    params = {"page": 1, "limit": 50, "mode": "osu"}
    query_string = client.format_query_parameters(params)

    assert query_string == "?page=1&limit=50&mode=osu"


def _future_expires_at() -> int:
    return int(time.time()) + 3600


@pytest.mark.asyncio
async def test_invalidate_token_clears_memory_and_redis(mock_redis_client: MagicMock) -> None:
    from app.osu_api.client.base import OsuAPIClientBase
    from app.redis_client import Namespace
    from app.redis_client.models import OsuClientOAuthToken

    client = OsuAPIClientBase(mock_redis_client)
    client._token = OsuClientOAuthToken(
        access_token="stale_token",
        token_type="Bearer",
        expires_in=3600,
        expires_at=_future_expires_at(),
    )

    await client.invalidate_token()

    assert client._token is None
    mock_redis_client.delete.assert_awaited_once_with(Namespace.OSU_CLIENT_OAUTH_TOKEN.value)


@pytest.mark.asyncio
async def test_authorized_request_retries_once_on_401(mock_redis_client: MagicMock) -> None:
    from app.osu_api.client.base import OsuAPIClientBase
    from app.redis_client.models import OsuClientOAuthToken

    client = OsuAPIClientBase(mock_redis_client)
    client._token = OsuClientOAuthToken(
        access_token="stale_token",
        token_type="Bearer",
        expires_in=3600,
        expires_at=_future_expires_at(),
    )
    client._http_client = MagicMock()
    client._http_client.request = AsyncMock(side_effect=[_mock_response(401), _mock_response(200)])

    url = "https://osu.ppy.sh/api/v2/users/123"
    with patch.object(client, "_oauth") as mock_oauth:
        mock_oauth.fetch_token = AsyncMock(
            return_value={
                "access_token": "fresh_token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "expires_at": str(_future_expires_at()),
            }
        )
        response = await client._authorized_request("GET", url)

    assert response.status_code == 200
    assert client._http_client.request.await_count == 2
    assert client._token is not None
    assert client._token.access_token == "fresh_token"

    first_call, retry_call = client._http_client.request.await_args_list
    assert first_call.kwargs["headers"]["Authorization"] == "Bearer stale_token"
    assert retry_call.kwargs["headers"]["Authorization"] == "Bearer fresh_token"

    mock_oauth.fetch_token.assert_awaited_once()
    mock_redis_client.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_authorized_request_does_not_retry_on_other_status(
    mock_redis_client: MagicMock,
) -> None:
    from app.osu_api.client.base import OsuAPIClientBase
    from app.redis_client.models import OsuClientOAuthToken

    client = OsuAPIClientBase(mock_redis_client)
    client._token = OsuClientOAuthToken(
        access_token="valid_token",
        token_type="Bearer",
        expires_in=3600,
        expires_at=_future_expires_at(),
    )
    client._http_client = MagicMock()
    client._http_client.request = AsyncMock(return_value=_mock_response(404))

    with patch.object(client, "_oauth") as mock_oauth:
        mock_oauth.fetch_token = AsyncMock(side_effect=Exception("Should not be called"))
        response = await client._authorized_request("GET", "https://osu.ppy.sh/api/v2/users/123")

    assert response.status_code == 404
    client._http_client.request.assert_awaited_once()
    mock_redis_client.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_authorized_request_stops_after_single_retry(mock_redis_client: MagicMock) -> None:
    from app.osu_api.client.base import OsuAPIClientBase
    from app.redis_client.models import OsuClientOAuthToken

    client = OsuAPIClientBase(mock_redis_client)
    client._token = OsuClientOAuthToken(
        access_token="stale_token",
        token_type="Bearer",
        expires_in=3600,
        expires_at=_future_expires_at(),
    )
    client._http_client = MagicMock()
    client._http_client.request = AsyncMock(side_effect=[_mock_response(401), _mock_response(401)])

    with patch.object(client, "_oauth") as mock_oauth:
        mock_oauth.fetch_token = AsyncMock(
            return_value={
                "access_token": "fresh_token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "expires_at": str(_future_expires_at()),
            }
        )
        response = await client._authorized_request("GET", "https://osu.ppy.sh/api/v2/users/123")

    assert response.status_code == 401
    assert client._http_client.request.await_count == 2
    mock_oauth.fetch_token.assert_awaited_once()


@pytest.mark.asyncio
async def test_authorized_request_with_explicit_token_does_not_retry_on_401(
    mock_redis_client: MagicMock,
) -> None:
    from app.osu_api.client.base import OsuAPIClientBase

    client = OsuAPIClientBase(mock_redis_client)
    client._http_client = MagicMock()
    client._http_client.request = AsyncMock(return_value=_mock_response(401))

    response = await client._authorized_request(
        "GET", "https://osu.ppy.sh/api/v2/me", access_token="user_token"
    )

    assert response.status_code == 401
    client._http_client.request.assert_awaited_once()
    mock_redis_client.delete.assert_not_awaited()

    request_headers = client._http_client.request.await_args.kwargs["headers"]
    assert request_headers["Authorization"] == "Bearer user_token"
