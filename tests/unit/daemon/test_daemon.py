from unittest.mock import AsyncMock

import pytest

from app.config import ServiceSettings
from app.daemon import Daemon
from app.daemon.services import (
    ProfileFetcher,
    QueueRequestHandler,
    RuleValidationService,
    ScoreFetcher,
)
from tests._helpers.mocks import mock_redis_client

ALL_SERVICES = {
    "profile_fetcher": ServiceSettings(enabled=True, interval_hours=168.0),
    "queue_request_handler": ServiceSettings(enabled=True),
    "score_fetcher": ServiceSettings(enabled=True, interval_hours=24.0),
    "rule_validation": ServiceSettings(enabled=True),
}


class TestDaemon:
    """Test Daemon service registration."""

    @pytest.fixture
    def rc(self) -> AsyncMock:
        """Return a mock Redis client."""
        return mock_redis_client()

    @pytest.fixture
    def db(self) -> AsyncMock:
        """Return a mock database."""
        return AsyncMock()

    async def test_on_start_registers_all_enabled_services(
        self, rc: AsyncMock, db: AsyncMock
    ) -> None:
        """Test that all enabled services are registered."""
        daemon = Daemon(rc, db, services=ALL_SERVICES)

        await daemon._on_start()

        assert set(daemon._services) == set(ALL_SERVICES)
        assert isinstance(daemon._services["profile_fetcher"], ProfileFetcher)
        assert isinstance(daemon._services["score_fetcher"], ScoreFetcher)
        assert isinstance(daemon._services["queue_request_handler"], QueueRequestHandler)
        assert isinstance(daemon._services["rule_validation"], RuleValidationService)

    async def test_on_start_skips_disabled_score_fetcher(
        self, rc: AsyncMock, db: AsyncMock
    ) -> None:
        """Test that a disabled score fetcher is not registered."""
        services = {
            **ALL_SERVICES,
            "score_fetcher": ServiceSettings(enabled=False, interval_hours=24.0),
        }
        daemon = Daemon(rc, db, services=services)

        await daemon._on_start()

        assert "score_fetcher" not in daemon._services
        assert set(daemon._services) == {
            "profile_fetcher",
            "queue_request_handler",
            "rule_validation",
        }

    async def test_on_start_skips_disabled_rule_validation(
        self, rc: AsyncMock, db: AsyncMock
    ) -> None:
        """Test that a disabled rule validation service is not registered."""
        services = {
            **ALL_SERVICES,
            "rule_validation": ServiceSettings(enabled=False),
        }
        daemon = Daemon(rc, db, services=services)

        await daemon._on_start()

        assert "rule_validation" not in daemon._services
        assert set(daemon._services) == {
            "profile_fetcher",
            "queue_request_handler",
            "score_fetcher",
        }

    async def test_on_start_skips_all_disabled_services(self, rc: AsyncMock, db: AsyncMock) -> None:
        """Test that no services are registered when all are disabled."""
        services = {name: ServiceSettings(enabled=False) for name in ALL_SERVICES}
        daemon = Daemon(rc, db, services=services)

        await daemon._on_start()

        assert daemon._services == {}

    async def test_profile_fetcher_uses_configured_interval(
        self, rc: AsyncMock, db: AsyncMock
    ) -> None:
        """Test that the profile fetcher interval is threaded into the scheduler."""
        services = {
            **ALL_SERVICES,
            "profile_fetcher": ServiceSettings(enabled=True, interval_hours=168.0),
        }
        daemon = Daemon(rc, db, services=services)

        await daemon._on_start()

        assert daemon._services["profile_fetcher"]._job_interval_hours == 168.0

    async def test_score_fetcher_uses_configured_interval(
        self, rc: AsyncMock, db: AsyncMock
    ) -> None:
        """Test that the score fetcher interval is threaded into the scheduler."""
        services = {
            **ALL_SERVICES,
            "score_fetcher": ServiceSettings(enabled=True, interval_hours=48.0),
        }
        daemon = Daemon(rc, db, services=services)

        await daemon._on_start()

        assert daemon._services["score_fetcher"]._job_interval_hours == 48.0
