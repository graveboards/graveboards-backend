import asyncio
from datetime import datetime, timedelta
from typing import ClassVar, Any
from abc import ABC

from app.redis import RedisClient
from app.database import PostgresqlDB
from app.database.models import Base
from app.utils import aware_utcnow
from app.logging import Logger
from app.osu_api import OsuAPIClient
from .scheduled import ScheduledService
from .job import JobLoadInstruction

DEFAULT_FETCH_CONCURRENCY = 5
DEFAULT_FETCH_INTERVAL_HOURS = 24.0
DEFAULT_FETCH_DISTRIBUTED_SPACING_SECONDS = 5.0
DEFAULT_PENDING_RECORD_TIMEOUT_SECONDS = 60.0
DEFAULT_FALLBACK_DELAY_HOURS = 24.0


class ScheduledFetcherService(ScheduledService, ABC):
    """Base class for services that fetch and synchronize entities.

    This class handles:
        - osu! API client initialization
        - Rate limit enforcement

    Subclasses must define the ``LOGGER``, ``RECORD_MODEL``, ``CHANNEL``, and
    optionally ``JOB_NAME`` class variables.
    """

    LOGGER: ClassVar[Logger | None] = None
    RECORD_MODEL: ClassVar[type[Base] | None] = None
    CHANNEL: ClassVar[str | None] = None
    JOB_NAME: ClassVar[str] = "fetch"

    def __init__(
        self,
        rc: RedisClient,
        db: PostgresqlDB,
        *,
        fetch_concurrency: int = DEFAULT_FETCH_CONCURRENCY,
        fetch_interval_hours: float = DEFAULT_FETCH_INTERVAL_HOURS,
        fetch_distributed_spacing_seconds: float = DEFAULT_FETCH_DISTRIBUTED_SPACING_SECONDS,
        pending_record_timeout_seconds: float = DEFAULT_PENDING_RECORD_TIMEOUT_SECONDS,
        fallback_delay_hours: float = DEFAULT_FALLBACK_DELAY_HOURS
    ) -> None:
        """
        Initialize the service.

        Args:
            rc:
                Redis client used for pub/sub coordination and distributed
                synchronization.
            db:
                PostgreSQL database interface used for managing persistent data
                retrieved from the osu! API.
            fetch_concurrency:
                Maximum number of fetch operations allowed to run concurrently. This
                limits outbound osu! API requests and controls resource usage.
            fetch_interval_hours:
                Interval between successive fetches. After each fetch, the next
                execution time is scheduled based on this value.
            fetch_distributed_spacing_seconds:
                Amount of time to stagger scheduled fetches to reduce burst load when
                multiple workers are running. Helps control osu! API request pacing.
            pending_record_timeout_seconds:
                Maximum time the subscriber may wait on retrieving records from
                the database before rescheduling with ``fallback_delay_hours``.
            fallback_delay_hours:
                Amount of time to wait until attempting to reschedule fetches that the
                subscriber failed to load the record of.
        """
        super().__init__(
            rc,
            db,
            job_concurrency=fetch_concurrency,
            job_interval_hours=fetch_interval_hours,
            job_distributed_spacing_seconds=fetch_distributed_spacing_seconds
        )

        self._db = db
        self._oac = OsuAPIClient(self._rc)
        self._pending_record_timeout_seconds = pending_record_timeout_seconds
        self._fallback_delay_hours = fallback_delay_hours
        self._rate_lock = asyncio.Lock()
        self._last_request_time: datetime | None = None

    async def _resolve_job_instruction(self, record_id: int) -> JobLoadInstruction | None:
        try:
            record = await self._get_pending_record(record_id)
            return JobLoadInstruction(last_execution=record.last_fetch)
        except TimeoutError:
            self.logger.warning(
                f"Timed out while waiting to get pending {self.RECORD_MODEL.__name__} with id %s; scheduling fallback execution",
                record_id,
            )

            fallback_time = aware_utcnow() + timedelta(hours=self._fallback_delay_hours)
            return JobLoadInstruction(execution_time=fallback_time)

    async def _get_pending_record(
        self,
        record_id: int,
        timeout: float = None,
        interval_seconds: float = 0.5
    ) -> Any:
        """Wait for a pending record to become available.

        Polls the database until the record exists or the timeout expires.

        Args:
            record_id:
                ID of the record.
            timeout:
                Maximum number of seconds to wait.

        Returns:
            The matching record model.

        Raises:
            TimeoutError: If the record is not found within the timeout.
        """
        if timeout is None:
            timeout = self._pending_record_timeout_seconds

        start_time = aware_utcnow()

        while (aware_utcnow() - start_time).total_seconds() < timeout:
            record = await self._db.get(self.RECORD_MODEL, id=record_id)

            if record:
                return record

            await asyncio.sleep(interval_seconds)

        raise TimeoutError

    async def _on_job_success(self, record_id: int) -> None:
        """Update the record's last fetch"""
        await self._db.update(self.RECORD_MODEL, record_id, last_fetch=aware_utcnow())

    async def _respect_rate_limit(self) -> None:
        """Ensure minimum delay between outbound API requests."""
        async with self._rate_lock:
            now = aware_utcnow()

            if self._last_request_time is not None:
                elapsed = (now - self._last_request_time).total_seconds()
                remaining = self._job_distributed_spacing_seconds - elapsed

                if remaining > 0:
                    await asyncio.sleep(remaining)

            self._last_request_time = aware_utcnow()
