import asyncio
import heapq
from datetime import datetime, timedelta, timezone
from typing import ClassVar
from abc import ABC, abstractmethod

from app.database import PostgresqlDB
from app.logging import Logger
from app.redis import RedisClient
from app.utils import aware_utcnow
from .service import Service
from .job import JobLoadInstruction

DEFAULT_JOB_CONCURRENCY = 5
DEFAULT_JOB_INTERVAL_HOURS = 24.0
DEFAULT_JOB_DISTRIBUTED_SPACING_SECONDS = 0.0


class ScheduledService(Service, ABC):
    """Base class for services with job scheduling.

    This class handles:
        - Job scheduling via priority heap
        - Redis pub/sub subscription
        - Automatic rescheduling
        - Concurrency limiting

    Subclasses must define the ``LOGGER``, ``CHANNEL``, and optionally ``JOB_NAME``
    class variables.
    """

    LOGGER: ClassVar[Logger | None] = None
    CHANNEL: ClassVar[str | None] = None
    JOB_NAME: ClassVar[str] = "job"

    def __init__(
        self,
        rc: RedisClient,
        db: PostgresqlDB,
        *,
        job_concurrency: int = DEFAULT_JOB_CONCURRENCY,
        job_interval_hours: float = DEFAULT_JOB_INTERVAL_HOURS,
        job_distributed_spacing_seconds: float = DEFAULT_JOB_DISTRIBUTED_SPACING_SECONDS
    ) -> None:
        """
        Initialize the service.

        Args:
            rc:
                Redis client used for pub/sub coordination and distributed
                synchronization.
            db:
                PostgreSQL database interface used for managing persistent data.
            job_concurrency:
                Maximum number of job procedures allowed to run concurrently.
            job_interval_hours:
                Interval between successive job executions. After each one, the next
                execution time is scheduled based on this value.
            job_distributed_spacing_seconds:
                Amount of time to stagger scheduled jobs to reduce burst load when
                multiple workers are running.
        """
        super().__init__()

        if self.CHANNEL is None:
            raise TypeError("Subclasses must define the CHANNEL class variable")

        self._rc = rc
        self._db = db
        self._job_semaphore = asyncio.Semaphore(job_concurrency)
        self._job_interval_hours = job_interval_hours
        self._job_distributed_spacing_seconds = job_distributed_spacing_seconds
        self._pubsub = self._rc.pubsub()
        self._job_heap: list[tuple[datetime, int]] = []
        self._active_job_ids: set[int] = set()
        self._job_condition = asyncio.Condition()

    async def _on_start(self) -> None:
        """Set up the service.

        Preloads scheduled jobs and register scheduler and subscriber service tasks.
        """
        await self._preload_jobs()
        await self.register_task("job_scheduler", self._job_scheduler, critical=True)
        await self.register_task("job_subscriber", self._job_subscriber, critical=True)
        await self._pubsub.subscribe(self.CHANNEL)

    async def _on_stop(self) -> None:
        """Notify tasks to stop."""
        await self._pubsub.unsubscribe()

        async with self._job_condition:
            self._job_condition.notify_all()

    async def _on_stopped(self) -> None:
        """Perform final cleanup."""
        await self._pubsub.close()

    async def _job_scheduler(self) -> None:
        """Continuously schedule and execute jobs.

        Waits for jobs to become available in the priority queue and spawns
        asynchronous workers to handle them.
        """
        while not self._stop_event.is_set():
            async with self._job_condition:
                while not self._job_heap and not self._stop_event.is_set():
                    await self._job_condition.wait()

                if self._stop_event.is_set():
                    break

                execution_time, job_id = heapq.heappop(self._job_heap)

            if job_id in self._active_job_ids:
                continue

            self._active_job_ids.add(job_id)
            self.create_ephemeral_task(
                self._handle_job(job_id, execution_time),
                name=f"{self.JOB_NAME}-{job_id}"
            )

    async def _job_subscriber(self) -> None:
        """Listen for and load new jobs via Redis pub/sub."""
        async for message in self._pubsub.listen():
            if self._stop_event.is_set():
                break

            if message["type"] != "message" or message["channel"] != self.CHANNEL:
                continue

            job_id = int(message["data"])

            try:
                instruction = await self._resolve_job_instruction(job_id)
            except Exception:
                self.logger.exception(
                    f"{self.__class__.__name__}.{self._resolve_job_instruction.__name__} "
                    f"raised for {job_id=}"
                )
                continue

            async with self._job_condition:
                await self._load_job(job_id, instruction=instruction)
                self.logger.debug(f"Loaded job: {job_id}")
                self._job_condition.notify()

    async def _resolve_job_instruction(self, job_id: int) -> JobLoadInstruction | None:
        """Execute before the job is loaded to provide instruction.

        Subclasses can override to configure scheduling behavior of new jobs on a
        case-by-case basis as they arrive from the subscriber.
        """
        pass

    async def _preload_jobs(self) -> None:
        """Load jobs into the scheduler at startup.

        Subclasses can override this to provide implementation.
        """
        pass

    async def _load_job(
        self,
        job_id: int,
        *,
        instruction: JobLoadInstruction | None = None
    ) -> None:
        """Schedule a job for future execution.

        The job is inserted into the scheduler's priority queue according to the
        provided ``JobLoadInstruction``.

        Scheduling rules:

        If ``instruction`` is ``None``:
            The job is appended to the end of the current queue.
        If ``instruction.skip`` is ``True``:
            The job is not scheduled.
        If ``instruction.execution_time`` is set:
            The job is scheduled accordingly.
        If ``instruction.last_execution`` is None:
            The job is scheduled for immediate execution.
        Otherwise:
            The next execution time is computed as ``last_execution`` +
            ``interval_hours`` where ``interval_hours`` defaults to the scheduler's
            configured interval if not provided in ``instruction``.

        Args:
            job_id:
                Unique identifier for the job.
            instruction:
                Optional object controlling scheduling behavior.

        Raises:
            TypeError: If the ``instruction`` value is invalid.
        """
        if instruction is None:
            execution_time = self._get_latest_execution_time() + timedelta(microseconds=1)
        else:
            if not isinstance(instruction, JobLoadInstruction):
                raise TypeError(f"Arg 'instruction' must be None or {JobLoadInstruction.__name__}, got {type(instruction).__name__}")

            if instruction.skip:
                return

            if instruction.execution_time is not None:
                execution_time = instruction.execution_time
            elif instruction.last_execution is None:
                execution_time = aware_utcnow()
            else:
                interval = instruction.interval_hours or self._job_interval_hours
                execution_time = instruction.last_execution.replace(tzinfo=timezone.utc) + timedelta(hours=interval)

        heapq.heappush(self._job_heap, (execution_time, job_id))

    async def _handle_job(self, job_id: int, execution_time: datetime) -> None:
        """Execute a scheduled job.

        Waits until the scheduled execution time, executes the job, and reschedules it.

        Args:
            job_id:
                Identifier of the job.
            execution_time:
                When the job should execute.
        """
        delay = (execution_time - aware_utcnow()).total_seconds()

        if delay > 0:
            await asyncio.sleep(delay)

        try:
            async with self._job_semaphore:
                await self._execute_job(job_id)
        except Exception as exc:
            self.logger.exception(
                f"{self.__class__.__name__}.{self._execute_job.__name__} "
                f"failed for {job_id=}"
            )
            await self._safe_hook(self._on_job_error, job_id, exc)
        else:
            await self._safe_hook(self._on_job_success, job_id)

        next_execution_time = aware_utcnow() + timedelta(hours=self._job_interval_hours)

        async with self._job_condition:
            heapq.heappush(self._job_heap, (next_execution_time, job_id))
            self._active_job_ids.discard(job_id)
            await self._safe_hook(self._on_job_finish, job_id)
            self._job_condition.notify()

    async def _on_job_success(self, job_id: int) -> None:
        """Execute after a job has completed successfully.

         Subclasses can override this to perform post-success work.

         Args:
             job_id:
                 Identifier of the job.
         """
        pass

    async def _on_job_error(self, job_id: int, exc: Exception) -> None:
        """Execute after a job failed due to an exception.

        Subclasses can override this to perform logging, alerting, or metrics.

        Args:
            job_id:
                Identifier of the job.
            exc:
                Exception that was raised from the job.
        """
        self.logger.error(f"Job with ID '{job_id}' failed with error: {exc}", exc_info=True)

    async def _on_job_finish(self, job_id: int) -> None:
        """Execute after a job has finished.

         Subclasses can override this to perform cleanup work.

         Args:
             job_id:
                 Identifier of the job.
         """
        pass

    @abstractmethod
    async def _execute_job(self, job_id: int) -> None:
        """Perform the scheduled job procedure.

        Subclasses must override this to provide implementation

        Args:
            job_id:
                Identifier of the job.
        """
        ...

    def _get_latest_execution_time(self) -> datetime:
        if not self._job_heap:
            return aware_utcnow()

        return max(self._job_heap, key=lambda x: x[0])[0]
