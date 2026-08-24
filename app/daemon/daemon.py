"""Daemon entry point and service registration."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from app.config import CONFIG, ServiceSettings
from app.observability.logging import get_logger

from .services import (
    ProfileFetcher,
    QueueRequestHandler,
    RuleValidationService,
    ScoreFetcher,
    ServiceFactory,
)
from .services.service.scheduled_fetcher import (
    DEFAULT_FETCH_CONCURRENCY,
    DEFAULT_FETCH_DISTRIBUTED_SPACING_SECONDS,
    DEFAULT_FETCH_INTERVAL_HOURS,
)
from .supervisor import ServiceSupervisor

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from app.database import PostgresqlDB
    from app.observability.logging import Logger
    from app.redis_client import RedisClient

    from .services import Service

    _ServiceFactory = Callable[[ServiceSettings], "Service"]


class Daemon(ServiceSupervisor):
    """Supervisor for the app's required background services.

    Services are configured through a per-service ``ServiceSettings`` mapping.
    Disabled services are skipped entirely; interval-driven services (the
    fetchers) are scheduled using their configured interval in hours.
    """

    LOGGER: ClassVar[Logger] = get_logger(__name__)

    def __init__(
        self,
        rc: RedisClient,
        db: PostgresqlDB,
        *,
        services: Mapping[str, ServiceSettings] | None = None,
    ) -> None:
        """Initialize the daemon.

        Args:
            rc:
                Redis client used for pub/sub coordination and distributed
                synchronization.
            db:
                PostgreSQL database interface used for managing persistent data.
            services:
                Per-service configuration keyed by service name. Defaults to
                ``CONFIG.SERVICES``.
        """
        super().__init__()
        self._rc = rc
        self._db = db
        self._service_settings = dict(services) if services is not None else dict(CONFIG.SERVICES)
        self._service_factories: dict[str, _ServiceFactory] = {
            "profile_fetcher": lambda settings: ProfileFetcher(
                self._rc,
                self._db,
                fetch_concurrency=settings.fetch_concurrency or DEFAULT_FETCH_CONCURRENCY,
                fetch_interval_hours=settings.interval_hours or DEFAULT_FETCH_INTERVAL_HOURS,
                fetch_distributed_spacing_seconds=settings.request_spacing_seconds
                or DEFAULT_FETCH_DISTRIBUTED_SPACING_SECONDS,
            ),
            "score_fetcher": lambda settings: ScoreFetcher(
                self._rc,
                self._db,
                fetch_interval_hours=settings.interval_hours or DEFAULT_FETCH_INTERVAL_HOURS,
            ),
            "queue_request_handler": lambda _settings: QueueRequestHandler(self._rc, self._db),
            "rule_validation": lambda _settings: RuleValidationService(self._rc, self._db),
        }

    def _build_service(self, name: str) -> Service:
        """Build a service instance for the given service name.

        Args:
            name:
                Unique identifier for the service.

        Returns:
            A configured service instance.
        """
        settings = self._service_settings[name]
        return self._service_factories[name](settings)

    def _make_factory(self, name: str) -> ServiceFactory:
        """Create a zero-argument factory for the given service name.

        Args:
            name:
                Unique identifier for the service.

        Returns:
            A factory that builds the configured service instance.
        """

        def factory() -> Service:
            return self._build_service(name)

        return factory

    async def _on_start(self) -> None:
        """Set up the daemon."""
        for name, settings in self._service_settings.items():
            if not settings.enabled:
                self.logger.info(f"Skipping {name}: disabled by configuration")
                continue

            if name not in self._service_factories:
                self.logger.warning(f"Skipping {name}: no factory registered for service")
                continue

            await self.register_service(name, self._make_factory(name))

        self.logger.info(f"Starting up daemon: loading registered services ({len(self._services)})")

    async def _on_started(self) -> None:
        """Log service startups."""
        for service in self._services.values():
            class_name = service.__class__.__name__
            self.logger.info(f"Started service: {class_name}")

    async def _on_stop(self) -> None:
        """Log daemon shutdown."""
        self.logger.info(f"Shutting down daemon: terminating service tasks ({len(self._services)})")
        await super()._on_stop()
