from typing import ClassVar

from app.redis import RedisClient
from app.database import PostgresqlDB
from app.logging import get_logger, Logger
from .supervisor import ServiceSupervisor
from .services import ProfileFetcher, QueueRequestHandler, ScoreFetcher


class Daemon(ServiceSupervisor):
    """Supervisor for the app's required background services.

    Registers and runs the following services:
        - ``ProfileFetcher``
        - ``QueueRequestHandler``
        - ``ScoreFetcher``
    """

    LOGGER: ClassVar[Logger] = get_logger(__name__)

    def __init__(self, rc: RedisClient, db: PostgresqlDB):
        """Initialize the daemon.

        Args:
            rc:
                Redis client used for pub/sub coordination and distributed
                synchronization.
            db:
                PostgreSQL database interface used for managing persistent data.
        """
        super().__init__()
        self._rc = rc
        self._db = db

    async def _on_start(self) -> None:
        """Set up the daemon."""
        await self.register_service("profile_fetcher", lambda: ProfileFetcher(self._rc, self._db))
        await self.register_service("queue_request_handler", lambda: QueueRequestHandler(self._rc, self._db))
        await self.register_service("score_fetcher", lambda: ScoreFetcher(self._rc, self._db))
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
