"""Unit tests for the /api/v1/health endpoint."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_health_deps() -> dict[str, MagicMock]:
    """Return mocks for the health check's external dependencies."""
    mock_db = MagicMock()
    mock_db.test_connection = AsyncMock()
    mock_db.close = AsyncMock()

    mock_rc = MagicMock()
    mock_rc.ping = AsyncMock(return_value=True)
    mock_rc.aclose = AsyncMock()

    mock_client = MagicMock()
    mock_client.rc = mock_rc
    mock_client.get_token = AsyncMock(return_value="cached_token")
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    return {"db": mock_db, "rc": mock_rc, "client": mock_client}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_health_check_uses_cached_token_not_refresh(
    mock_health_deps: dict[str, MagicMock],
) -> None:
    """Health checks must use the cached osu! token, not force a refresh."""
    from api.v1.health import health_check

    deps = mock_health_deps
    mock_daemon = MagicMock()
    mock_daemon._services = {}

    with (
        patch("api.v1.health.PostgresqlDB", return_value=deps["db"]),
        patch("api.v1.health.RedisClient", return_value=deps["rc"]),
        patch("app.osu_api.OsuAPIClient", return_value=deps["client"]),
        patch("api.v1.health.request", MagicMock()) as mock_request,
    ):
        mock_request.state.daemon = mock_daemon
        result = await health_check()

    assert result["status"] in {"healthy", "degraded"}
    deps["client"].get_token.assert_awaited_once()
    assert deps["client"].refresh_token.call_count == 0
    assert deps["client"].__aenter__.await_count == 1
