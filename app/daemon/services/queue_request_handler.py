import asyncio

from httpx import ConnectTimeout

from app.beatmaps import BeatmapManager
from app.database.models import Request
from app.database.schemas import RequestSchema
from app.redis import ChannelName, Namespace
from app.redis.models import QueueRequestHandlerTask
from app.utils import aware_utcnow
from app.logging import get_logger
from .decorators import auto_retry
from .enums import RuntimeTaskName
from .service import Service

logger = get_logger(__name__)


class QueueRequestHandler(Service):
    def __init__(self, *args):
        super().__init__(*args)

        self.pubsub = self.rc.pubsub()

        self.task_queue: asyncio.Queue[QueueRequestHandlerTask] = asyncio.Queue()
        self.tasks: dict[int, asyncio.Task] = {}
        self.task_condition = asyncio.Condition()

    async def run(self):
        self.runtime_tasks[RuntimeTaskName.SCHEDULER_TASK] = asyncio.create_task(self.task_scheduler(), name="Scheduler Task")
        self.runtime_tasks[RuntimeTaskName.SUBSCRIBER_TASK] = asyncio.create_task(self.task_subscriber(), name="Subscriber Task")
        await asyncio.gather(*self.runtime_tasks.values())

    async def task_scheduler(self):
        while True:
            async with self.task_condition:
                while self.task_queue.empty():
                    await self.task_condition.wait()

                task = await self.task_queue.get()

            scheduled_task = asyncio.create_task(self.handle_queue_request(task))
            self.tasks[task.hashed_id] = scheduled_task
            scheduled_task.add_done_callback(self.handle_task_error)

    async def task_subscriber(self):
        await self.pubsub.subscribe(ChannelName.QUEUE_REQUEST_HANDLER_TASKS.value)

        async for message in self.pubsub.listen():
            if not message["type"] == "message" or not message["channel"] == ChannelName.QUEUE_REQUEST_HANDLER_TASKS.value:
                continue

            task_id = int(message["data"])
            task_hash_name = Namespace.QUEUE_REQUEST_HANDLER_TASK.hash_name(task_id)
            serialized_task = await self.rc.hgetall(task_hash_name)
            task = QueueRequestHandlerTask.deserialize(serialized_task)

            async with self.task_condition:
                await self.task_queue.put(task)
                self.task_condition.notify()

    @staticmethod
    def handle_task_error(task: asyncio.Task):
        try:
            task.result()
        except Exception as e:
            logger.error(f"Task '{task.get_name()}' failed with error: {e}", exc_info=True)

    @auto_retry(retry_exceptions=(ConnectTimeout,))
    async def handle_queue_request(self, task: QueueRequestHandlerTask):
        try:
            bm = BeatmapManager(self.rc, self.db)
            await bm.archive(task.beatmapset_id)

            request_dict = RequestSchema.model_validate(task).model_dump(
                exclude={"user_profile", "queue"}
            )
            request = await self.db.add(Request, **request_dict)
            logger.debug(f"Added request id={request.id} for beatmapset {request.beatmapset_id} to queue id={request.queue_id}")

            task_hash_name = Namespace.QUEUE_REQUEST_HANDLER_TASK.hash_name(task.hashed_id)
            await self.rc.hset(task_hash_name, "completed_at", aware_utcnow().isoformat())
        except Exception:
            task_hash_name = Namespace.QUEUE_REQUEST_HANDLER_TASK.hash_name(task.hashed_id)
            await self.rc.hset(task_hash_name, "failed_at", aware_utcnow().isoformat())
            raise
