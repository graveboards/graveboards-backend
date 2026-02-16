import asyncio
import heapq
from datetime import datetime, timedelta, timezone

from httpx import ConnectTimeout, HTTPStatusError, ReadTimeout

from app.osu_api import OsuAPIClient
from app.database.models import ProfileFetcherTask, User, Profile
from app.database.schemas import ProfileSchema
from app.redis import ChannelName, Namespace, LOCK_EXPIRY
from app.utils import aware_utcnow
from app.exceptions import RedisLockTimeoutError
from app.logging import get_logger
from .decorators import auto_retry
from .enums import RuntimeTaskName
from .service import Service

PROFILE_FETCHER_INTERVAL_HOURS = 24
PROFILE_FETCHER_MIN_INTERVAL_SECONDS = 5
PENDING_TASK_TIMEOUT_SECONDS = 60
logger = get_logger(__name__, prefix="ProfileFetcher")


class ProfileFetcher(Service):
    def __init__(self, *args):
        super().__init__(*args)

        self.pubsub = self.rc.pubsub()
        self.oac = OsuAPIClient(self.rc)

        self.task_heap: list[tuple[datetime, int]] = []
        self.tasks: dict[int, asyncio.Task] = {}
        self.task_condition = asyncio.Condition()

        self._rate_lock = asyncio.Lock()
        self._last_request_time: datetime | None = None

    async def run(self):
        await self.preload_tasks()
        self.runtime_tasks[RuntimeTaskName.SCHEDULER_TASK] = asyncio.create_task(self.task_scheduler(), name="Scheduler Task")
        self.runtime_tasks[RuntimeTaskName.SUBSCRIBER_TASK] = asyncio.create_task(self.task_subscriber(), name="Subscriber Task")
        await asyncio.gather(*self.runtime_tasks.values())

    async def task_scheduler(self):
        while True:
            async with self.task_condition:
                while not self.task_heap:
                    await self.task_condition.wait()

                execution_time, task_id = heapq.heappop(self.task_heap)

            scheduled_task = asyncio.create_task(self.handle_task(execution_time, task_id))
            self.tasks[task_id] = scheduled_task
            scheduled_task.add_done_callback(self.handle_task_error)

    async def task_subscriber(self):
        await self.pubsub.subscribe(ChannelName.PROFILE_FETCHER_TASKS.value)

        async for message in self.pubsub.listen():
            if not message["type"] == "message" or not message["channel"] == ChannelName.PROFILE_FETCHER_TASKS.value:
                continue

            task_id = int(message["data"])

            try:
                task = await self.get_pending_task(task_id)
            except TimeoutError:
                logger.warning(f"Timed out while waiting to get pending profile fetcher task {task_id}, skipping")
                continue

            if task.enabled:
                async with self.task_condition:
                    self.load_task(task)
                    self.task_condition.notify()

                info = {"id": task.id, "user_id": task.user_id}
                logger.debug(f"Loaded task: {info}")

    async def preload_tasks(self):
        tasks = await self.db.get_many(ProfileFetcherTask, enabled=True)
        missing_profile_user_ids = await self.db.get_many(User, profile=None, _select="id")

        for task in tasks:
            self.load_task(task, now=task.user_id in missing_profile_user_ids)

        logger.debug(f"Preloaded tasks: ({len(tasks)})")

    def load_task(self, task: ProfileFetcherTask, now: bool = False):
        if not task.enabled:
            return

        if task.last_fetch is not None and not now:
            execution_time = task.last_fetch.replace(tzinfo=timezone.utc) + timedelta(hours=PROFILE_FETCHER_INTERVAL_HOURS)
        else:
            execution_time = aware_utcnow()

        heapq.heappush(self.task_heap, (execution_time, task.id))

    async def get_pending_task(self, task_id: int, timeout: int = PENDING_TASK_TIMEOUT_SECONDS) -> ProfileFetcherTask:
        start_time = aware_utcnow()

        while (aware_utcnow() - start_time).total_seconds() < timeout:
            task = await self.db.get(ProfileFetcherTask, id=task_id)

            if task:
                return task

            await asyncio.sleep(0.5)

        raise TimeoutError

    async def handle_task(self, execution_time: datetime, task_id: int):
        delay = (execution_time - aware_utcnow()).total_seconds()

        if delay > 0:
            await asyncio.sleep(delay)

        await self.fetch_profile(task_id)
        fetch_time = aware_utcnow()
        next_execution_time = fetch_time + timedelta(hours=PROFILE_FETCHER_INTERVAL_HOURS)
        await self.db.update(ProfileFetcherTask, task_id, last_fetch=fetch_time)

        async with self.task_condition:
            heapq.heappush(self.task_heap, (next_execution_time, task_id))
            self.task_condition.notify()

    @staticmethod
    def handle_task_error(task: asyncio.Task):
        try:
            task.result()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Task '{task.get_name()}' failed with error: {e}", exc_info=True)

    @auto_retry(retry_exceptions=(ConnectTimeout,))
    async def fetch_profile(self, task_id: int):
        if not (task := await self.db.get(ProfileFetcherTask, id=task_id)):
            raise ValueError(f"Task with ID '{task_id}' not found")

        user_id = task.user_id
        lock_hash_name = Namespace.LOCK.hash_name(Namespace.OSU_USER_PROFILE.hash_name(user_id))
        lock_acquired = await self.rc.set(lock_hash_name, "locked", ex=LOCK_EXPIRY, nx=True)

        if not lock_acquired:
            return

        try:
            async with self.rc.lock_ctx(lock_hash_name):
                await self._respect_rate_limit()
                user_dict = await self.oac.get_user(user_id)  # Rare httpx.readtimeout can occur, keeping note of that
                profile_dict = ProfileSchema.model_validate(user_dict).model_dump(
                    exclude={"id", "updated_at", "is_restricted"},
                    context={"jsonify_nested": True}
                )

                if not (profile := await self.db.get(Profile, user_id=user_id)):
                    profile = await self.db.add(Profile, **profile_dict)
                    info = {"id": profile.id, "user_id": user_id}
                    logger.debug(f"Fetched and added profile: {info}")
                else:
                    profile_dict["is_restricted"] = False  # Handle case of user getting unrestricted: 404 raised if restricted; thus, we can surmise no longer restricted
                    old_profile_dict = ProfileSchema.model_validate(profile).model_dump(context={"jsonify_nested": True})
                    delta = {}

                    for key, value in profile_dict.items():
                        old_value = old_profile_dict[key]

                        if key == "page" and old_value is not None:
                            if value.get("raw") != old_value.get("raw"):
                                delta[key] = value
                        elif value != old_value:
                            delta[key] = value

                    if delta:
                        await self.db.update(Profile, profile.id, **delta)
                        logger.debug(f"Fetched and updated profile for user {user_id}: {set(delta.keys())}")
                    else:
                        logger.debug(f"Profile fetched for user {user_id} is up-to-date")
        except RedisLockTimeoutError as e:
            logger.warning(str(e))
        except HTTPStatusError as e:
            logger.warning(
                f"HTTP error while fetching profile for user {user_id} - "
                f"Status: {e.response.status_code}, URL: '{e.request.url}', Detail: {e}"
            )
        except ReadTimeout as e:
            logger.warning(f"Read timeout while fetching profile for user {user_id}: {e}")

    async def _respect_rate_limit(self):
        async with self._rate_lock:
            now = aware_utcnow()

            if self._last_request_time is not None:
                elapsed = (now - self._last_request_time).total_seconds()
                remaining = PROFILE_FETCHER_MIN_INTERVAL_SECONDS - elapsed

                if remaining > 0:
                    await asyncio.sleep(remaining)

            self._last_request_time = aware_utcnow()
