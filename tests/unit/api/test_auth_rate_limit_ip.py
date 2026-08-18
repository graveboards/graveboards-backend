"""Unit tests for per-client-IP auth rate limiting.

Covers the X-Real-IP forwarding fix: the frontend calls the backend
container-to-container, so request.client.host is the frontend container for
every user. These tests assert the auth endpoints key rate limiting on the
forwarded X-Real-IP header instead.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.redis_client import RedisClient


def _make_request(client_host: str = "10.0.0.5", real_ip: str | None = "203.0.113.7") -> MagicMock:
    """Build a mock request with a container peer and optional X-Real-IP header."""
    mock_request = MagicMock()
    mock_request.client.host = client_host
    headers: dict[str, str] = {}
    if real_ip is not None:
        headers["X-Real-IP"] = real_ip
    mock_request.headers = headers
    mock_request.state.rc = MagicMock(spec=RedisClient)
    return mock_request


def _make_mock_redis() -> AsyncMock:
    """Create a mock Redis client."""
    mock_rc = AsyncMock(spec=RedisClient)
    mock_rc.ttl = AsyncMock(return_value=0)
    mock_rc.incr = AsyncMock(return_value=1)
    mock_rc.expire = AsyncMock(return_value=True)
    mock_rc.set = AsyncMock(return_value=True)
    mock_rc.delete = AsyncMock(return_value=1)
    mock_rc.getdel = AsyncMock(return_value="valid")
    return mock_rc


class TestExtractClientIp:
    """Unit tests for extract_client_ip."""

    @pytest.mark.unit
    def test_prefers_x_real_ip_header(self) -> None:
        from app.security.auth_rate_limit import extract_client_ip

        request = _make_request(client_host="10.0.0.5", real_ip="203.0.113.7")

        assert extract_client_ip(request) == "203.0.113.7"

    @pytest.mark.unit
    def test_takes_last_segment_of_forwarded_list(self) -> None:
        from app.security.auth_rate_limit import extract_client_ip

        request = _make_request(client_host="10.0.0.5", real_ip="198.51.100.4, 203.0.113.7")

        assert extract_client_ip(request) == "203.0.113.7"

    @pytest.mark.unit
    def test_falls_back_to_peer_when_header_missing(self) -> None:
        from app.security.auth_rate_limit import extract_client_ip

        request = _make_request(client_host="10.0.0.5", real_ip=None)

        assert extract_client_ip(request) == "10.0.0.5"

    @pytest.mark.unit
    def test_unknown_when_no_client(self) -> None:
        from app.security.auth_rate_limit import extract_client_ip

        request = MagicMock()
        request.client = None
        request.headers = {}

        assert extract_client_ip(request) == "unknown"


class TestLoginRateLimitKeysOnRealIp:
    """GET /api/v1/login must key its rate-limit window on X-Real-IP."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_login_uses_x_real_ip_not_container_ip(self) -> None:
        from api.v1.login import search

        mock_rc = _make_mock_redis()
        mock_request = _make_request(client_host="10.0.0.5", real_ip="203.0.113.7")

        with patch("api.v1.login.request", mock_request):
            await search(rc=mock_rc)

        assert mock_rc.incr.await_count == 1
        window_key = mock_rc.incr.await_args.args[0]
        assert "203.0.113.7" in window_key
        assert "10.0.0.5" not in window_key

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_login_falls_back_to_peer_without_header(self) -> None:
        from api.v1.login import search

        mock_rc = _make_mock_redis()
        mock_request = _make_request(client_host="10.0.0.5", real_ip=None)

        with patch("api.v1.login.request", mock_request):
            await search(rc=mock_rc)

        window_key = mock_rc.incr.await_args.args[0]
        assert "10.0.0.5" in window_key


class TestTokenRateLimitKeysOnRealIp:
    """POST /api/v1/token must key its rate-limit window on X-Real-IP."""

    TEST_USER_ID = 12345678
    TEST_STATE = "test_csrf_state_12345"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_post_token_uses_x_real_ip_not_container_ip(self) -> None:
        from api.v1.token import post

        mock_rc = _make_mock_redis()
        mock_request = _make_request(client_host="10.0.0.5", real_ip="203.0.113.7")

        with (
            patch("api.v1.token.request", mock_request),
            patch("api.v1.token.OAuth") as mock_oauth_cls,
            patch("api.v1.token.OsuAPIClient") as mock_client_cls,
        ):
            mock_oauth = mock_oauth_cls.return_value
            mock_oauth.fetch_token = AsyncMock(
                return_value={
                    "access_token": "test_access_token",
                    "refresh_token": "test_refresh_token",
                }
            )

            mock_client = mock_client_cls.return_value
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.get_own_data = AsyncMock(return_value={"id": self.TEST_USER_ID})

            mock_db = AsyncMock()
            mock_db.get = AsyncMock(
                side_effect=[
                    None,
                    MagicMock(enabled=False, last_fetch=None),
                ]
            )
            mock_db.add = AsyncMock()
            mock_db.update = AsyncMock()

            result = await post(
                body={"code": "test_code", "state": self.TEST_STATE},
                rc=mock_rc,
                db=mock_db,
            )

        assert result[1] == 201
        assert mock_rc.incr.await_count == 1
        window_key = mock_rc.incr.await_args.args[0]
        assert "203.0.113.7" in window_key
        assert "10.0.0.5" not in window_key

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_post_token_failure_uses_x_real_ip(self) -> None:
        from api.v1.token import post
        from app.exceptions import BadRequest

        mock_rc = _make_mock_redis()
        mock_request = _make_request(client_host="10.0.0.5", real_ip="203.0.113.7")

        with patch("api.v1.token.request", mock_request):
            with pytest.raises(BadRequest, match="Missing code"):
                await post(
                    body={"state": self.TEST_STATE},
                    rc=mock_rc,
                )

        for call in mock_rc.incr.await_args_list:
            key = call.args[0]
            assert "203.0.113.7" in key
            assert "10.0.0.5" not in key
