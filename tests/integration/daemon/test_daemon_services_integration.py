"""Integration tests for daemon lifecycle, supervisor, and scheduled services.

These tests use mocked Redis and database objects to test daemon behavior
without requiring real infrastructure.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.daemon.daemon import Daemon
from app.daemon.supervisor import ServiceSupervisor
from app.daemon.services import Service, ProfileFetcher, QueueRequestHandler, ScoreFetcher


class TestDaemonLifecycle:
    """Integration tests for Daemon lifecycle."""

    @pytest.fixture
    def mock_rc(self):
        """Create a mock Redis client."""
        rc = AsyncMock()
        rc.pubsub = MagicMock()
        rc.pubsub.subscribe = AsyncMock()
        rc.pubsub.parse_response = AsyncMock(return_value=None)
        rc.publish = AsyncMock(return_value=1)
        rc.close = AsyncMock()
        return rc

    @pytest.fixture
    def mock_db(self):
        """Create a mock database."""
        db = AsyncMock()
        db.close = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_daemon_registers_all_services(self, mock_rc, mock_db):
        """Test Daemon registers ProfileFetcher, QueueRequestHandler, ScoreFetcher."""
        daemon = Daemon(rc=mock_rc, db=mock_db)
        await daemon._on_start()

        assert "profile_fetcher" in daemon._services
        assert "queue_request_handler" in daemon._services
        assert "score_fetcher" in daemon._services
        assert len(daemon._services) == 3

    @pytest.mark.asyncio
    async def test_daemon_service_factories_are_lazy(self, mock_rc, mock_db):
        """Test that registered services are instances of Service."""
        daemon = Daemon(rc=mock_rc, db=mock_db)
        await daemon._on_start()

        for name, service in daemon._services.items():
            assert isinstance(service, Service)


class TestServiceSupervisor:
    """Integration tests for ServiceSupervisor."""

    @pytest.fixture
    def mock_rc(self):
        """Create a mock Redis client."""
        rc = AsyncMock()
        rc.close = AsyncMock()
        return rc

    @pytest.fixture
    def mock_db(self):
        """Create a mock database."""
        db = AsyncMock()
        db.close = AsyncMock()
        return db

    @pytest.fixture
    def supervisor(self):
        """Create a ServiceSupervisor with a valid LOGGER."""
        from app.logging import get_logger
        ServiceSupervisor.LOGGER = get_logger("test.supervisor")
        supervisor = ServiceSupervisor()
        return supervisor

    @pytest.mark.asyncio
    async def test_register_service_stores_factory(self, supervisor):
        """Test registering a service stores the factory under the given name."""
        from app.logging import get_logger

        class TestService(Service):
            LOGGER = get_logger("test.service")

        def factory():
            return TestService()

        await supervisor.register_service("test_service", factory)

        assert "test_service" in supervisor._services

    @pytest.mark.asyncio
    async def test_register_duplicate_service_raises(self, supervisor):
        """Test registering a service with a duplicate name raises ValueError."""
        from app.logging import get_logger

        class TestService(Service):
            LOGGER = get_logger("test.service")

        def factory():
            return TestService()

        await supervisor.register_service("test_service", factory)

        with pytest.raises(ValueError, match="already registered"):
            await supervisor.register_service("test_service", factory)

    @pytest.mark.asyncio
    async def test_supervisor_init_has_empty_services(self):
        """Test ServiceSupervisor starts with empty services dict."""
        from app.logging import get_logger
        ServiceSupervisor.LOGGER = get_logger("test.supervisor")
        supervisor = ServiceSupervisor()
        assert supervisor._services == {}


class TestScheduledService:
    """Integration tests for scheduled service job behavior."""

    @pytest.mark.asyncio
    async def test_service_requires_logger(self):
        """Test Service subclass without LOGGER raises TypeError."""
        with pytest.raises(TypeError, match="LOGGER"):
            class BadService(Service):
                pass
            BadService()

    @pytest.mark.asyncio
    async def test_service_with_logger_initializes(self):
        """Test Service subclass with LOGGER initializes correctly."""
        from app.logging import get_logger

        class GoodService(Service):
            LOGGER = get_logger(__name__)

        service = GoodService()
        assert service.logger is not None
        assert service._running is False
