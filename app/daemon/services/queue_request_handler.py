import json
from typing import ClassVar

from httpx import ConnectTimeout
from structlog.contextvars import bind_contextvars, clear_contextvars

from app.beatmaps import BeatmapManager
from app.database.crud.rules import RuleCRUD
from app.database.models import Request
from app.database.schemas import RequestSchema
from app.redis import ChannelName, Namespace
from app.redis.models import QueueRequestHandlerTask, QueueRequestValidationTask
from app.utils import aware_utcnow
from app.logging import get_logger, Logger
from .decorators import auto_retry
from .service import ScheduledService
from .service.job import JobLoadInstruction

logger = get_logger(__name__)


class QueueRequestHandler(ScheduledService):
    """Asynchronously offload posting requests to queues.

    This service handles processing requests before they are added to queues. This
    allows the beatmap manager to take as long as it needs to download and archive the
    beatmap attached to the request without blocking the API http exchange.

    When a request is posted to a queue, a handling job is sent that will be picked up
    by this service.
    """

    LOGGER: ClassVar[Logger] = get_logger(__name__, prefix="QueueRequestHandler")
    CHANNEL: ClassVar[str] = ChannelName.QUEUE_REQUEST_HANDLER_TASKS
    JOB_NAME: ClassVar[str] = "queue-request-handle"
    _should_reschedule: ClassVar[bool] = False

    async def _resolve_job_instruction(self, record_id: int) -> JobLoadInstruction | None:
        return JobLoadInstruction(execution_time=aware_utcnow())

    @auto_retry(retry_exceptions=(ConnectTimeout,))
    async def _execute_job(self, record_id: int):
        """Post a request to a queue.

        Retrieves relevant beatmapset data from the osu! API, creates or updates the
        corresponding records, and posts the request to the queue.

        Args:
            record_id:
                Identifier of the queue request handler job.

        Raises:
            ValueError: If the record does not exist.
        """
        hash_name = Namespace.QUEUE_REQUEST_HANDLER_TASK.hash_name(record_id)
        self.logger.debug(f"Executing QueueRequestHandler job {record_id}, looking up hash={hash_name}")

        try:
            serialized_record = await self._rc.hgetall(hash_name)

            if not serialized_record:
                self.logger.error(
                    f"QueueRequestHandlerTask with hashed ID '{record_id}' not found at {hash_name}"
                )
                raise ValueError(f"QueueRequestHandlerTask with hashed ID '{record_id}' not found")

            self.logger.debug(
                f"Found serialized record for {record_id}: keys={list(serialized_record.keys())}"
            )
            record = QueueRequestHandlerTask.deserialize(serialized_record)

            if record.http_request_id:
                bind_contextvars(request_id=record.http_request_id)

            self.logger.debug(
                f"Deserialized record: queue_id={record.queue_id}, beatmapset_id={record.beatmapset_id}, "
                f"user_id={record.user_id}"
            )

            try:
                bm = BeatmapManager(self._rc, self._db)
                self.logger.debug(f"Starting archive for beatmapset {record.beatmapset_id}")
                await bm.archive(record.beatmapset_id)
                self.logger.debug(f"Archive complete for beatmapset {record.beatmapset_id}")

                request_dict = RequestSchema.model_validate(record).model_dump(
                    exclude={"user_profile", "queue", "beatmapset_snapshot"}
                )
                self.logger.debug(f"Creating Request in DB with: {request_dict}")
                request = await self._db.add(Request, **request_dict)
                self.logger.debug(f"Added request id={request.id} for beatmapset {request.beatmapset_id} to queue id={request.queue_id}")

                await self._dispatch_validation_task(request.id, record.queue_id, record.beatmapset_id, record.http_request_id)

                await self._rc.hset(hash_name, "completed_at", aware_utcnow().isoformat())
                self.logger.debug(f"Marked {hash_name} as completed_at")
            finally:
                if record.http_request_id:
                    clear_contextvars()
        except Exception:
            self.logger.exception(f"Failed to execute QueueRequestHandler job {record_id}")
            await self._rc.hset(hash_name, "failed_at", aware_utcnow().isoformat())
            raise

    async def _dispatch_validation_task(self, request_id: int, queue_id: int, beatmapset_id: int, http_request_id: str = "") -> None:
        rules_snapshot = await self._snapshot_active_rules(queue_id)

        task = QueueRequestValidationTask(
            request_id=request_id,
            queue_id=queue_id,
            beatmapset_id=beatmapset_id,
            http_request_id=http_request_id,
            rules_snapshot=rules_snapshot,
        )
        task_hash_name = Namespace.QUEUE_REQUEST_HANDLER_TASK.hash_name(task.hashed_id)
        await self._rc.hset(task_hash_name, mapping=task.serialize())
        await self._rc.publish(ChannelName.QUEUE_REQUEST_VALIDATION_TASKS.value, task.hashed_id)

    async def _snapshot_active_rules(self, queue_id: int) -> str:
        crud = RuleCRUD()
        rules = await crud.get_rules(queue_id, only_active=True)
        snapshot = [
            {
                "id": rule.id,
                "type": rule.type,
                "version": rule.version,
                "config": rule.config or {},
                "is_active": rule.is_active,
            }
            for rule in rules
        ]
        return json.dumps(snapshot)
