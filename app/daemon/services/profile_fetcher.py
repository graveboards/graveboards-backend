from typing import ClassVar

from httpx import ConnectTimeout, HTTPStatusError, ReadTimeout

from app.database.models import ProfileFetcherTask, User, Profile, Base
from app.database.schemas import ProfileSchema
from app.redis import ChannelName, Namespace, LOCK_EXPIRY
from app.exceptions import RedisLockTimeoutError
from app.logging import get_logger, Logger
from app.utils import aware_utcnow
from .decorators import auto_retry
from .service import ScheduledFetcherService
from .service.job import JobLoadInstruction


class ProfileFetcher(ScheduledFetcherService):
    """Periodically fetch and synchronize osu! user profiles.

    This service schedules profile fetch jobs, listens for new jobs, and updates stored
    profile data from the osu! API.

    When a user is added elsewhere, a database event is triggered to send a fetch job
    that will be picked up by this service.
    """

    LOGGER: ClassVar[Logger] = get_logger(__name__, prefix="ProfileFetcher")
    RECORD_MODEL: ClassVar[type[Base]] = ProfileFetcherTask
    CHANNEL: ClassVar[str] = ChannelName.PROFILE_FETCHER_TASKS
    JOB_NAME: ClassVar[str] = "profile-fetch"

    async def _preload_jobs(self) -> None:
        """Load enabled profile fetch jobs into the scheduler at startup.

        Jobs for users without existing profiles are scheduled for immediate execution.
        """
        records = await self._db.get_many(ProfileFetcherTask, enabled=True)
        missing_profile_user_ids = await self._db.get_many(User, profile=None, _select="id")
        loaded = 0

        for record in records:
            if not record.enabled:
                continue

            if record.user_id in missing_profile_user_ids:
                execution_time = aware_utcnow()
            else:
                execution_time = None

            instruction = JobLoadInstruction(execution_time=execution_time, last_execution=record.last_fetch)
            await self._load_job(record.id, instruction=instruction)
            loaded += 1

        self.logger.debug(f"Preloaded jobs: ({loaded})")

    @auto_retry(retry_exceptions=(ConnectTimeout,))
    async def _execute_job(self, record_id: int) -> None:
        """Fetch and synchronize a user's osu! profile.

        Retrieves profile data from the osu! API, creates or updates the corresponding
        Profile record, and clears restricted status when applicable.

        A Redis lock is used to prevent concurrent fetches for the same user.

        Args:
            record_id:
                ID of the profile fetcher record.

        Raises:
            ValueError: If the record does not exist.
        """
        if not (record := await self._db.get(ProfileFetcherTask, id=record_id)):
            raise ValueError(f"ProfileFetcherTask with ID '{record_id}' not found")

        user_id = record.user_id
        lock_hash_name = Namespace.LOCK.hash_name(Namespace.OSU_USER_PROFILE.hash_name(user_id))
        lock_acquired = await self._rc.set(lock_hash_name, "locked", ex=LOCK_EXPIRY, nx=True)

        if not lock_acquired:
            # Another procedure is updating the user profile data
            return

        try:
            async with self._rc.lock_ctx(lock_hash_name):
                await self._respect_rate_limit()
                user_dict = await self._oac.get_user(user_id)  # Rare httpx.readtimeout can occur
                profile_dict = ProfileSchema.model_validate(user_dict).model_dump(
                    exclude={"id", "updated_at", "is_restricted"},
                    context={"jsonify_nested": True}
                )

                if not (profile := await self._db.get(Profile, user_id=user_id)):
                    profile = await self._db.add(Profile, **profile_dict)
                    info = {"id": profile.id, "user_id": user_id}
                    self.logger.debug(f"Fetched and added profile: {info}")
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
                        await self._db.update(Profile, profile.id, **delta)
                        self.logger.debug(f"Fetched and updated profile for user {user_id}: {set(delta.keys())}")
                    else:
                        self.logger.debug(f"Profile fetched for user {user_id} is up-to-date")
        except RedisLockTimeoutError as e:
            self.logger.warning(str(e))
        except HTTPStatusError as e:
            self.logger.warning(
                f"HTTP error while fetching profile for user {user_id} - "
                f"Status: {e.response.status_code}, URL: '{e.request.url}', Detail: {e}"
            )
            await self._db.update(ProfileFetcherTask, record_id, enabled=False)
        except ReadTimeout as e:
            self.logger.warning(f"Read timeout while fetching profile for user {user_id}: {e}")
