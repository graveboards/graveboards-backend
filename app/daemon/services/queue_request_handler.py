from typing import ClassVar

from httpx import ConnectTimeout

from app.beatmaps import BeatmapManager
from app.database.models import Request
from app.database.schemas import RequestSchema
from app.redis import ChannelName, Namespace
from app.redis.models import QueueRequestHandlerTask
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

        try:
            serialized_record = await self._rc.hgetall(hash_name)

            if not serialized_record:
                raise ValueError(f"QueueRequestHandlerTask with hashed ID '{record_id}' not found")

            record = QueueRequestHandlerTask.deserialize(serialized_record)

            bm = BeatmapManager(self._rc, self._db)
            await bm.archive(record.beatmapset_id)

            request_dict = RequestSchema.model_validate(record).model_dump(
                exclude={"user_profile", "queue"}
            )
            request = await self._db.add(Request, **request_dict)
            logger.debug(f"Added request id={request.id} for beatmapset {request.beatmapset_id} to queue id={request.queue_id}")

            await self._rc.hset(hash_name, "completed_at", aware_utcnow().isoformat())
        except Exception:
            await self._rc.hset(hash_name, "failed_at", aware_utcnow().isoformat())
            raise
