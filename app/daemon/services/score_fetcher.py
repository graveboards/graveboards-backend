from typing import ClassVar

from httpx import ConnectTimeout

from app.database.models import ScoreFetcherTask, Leaderboard
from app.redis import ChannelName
from app.logging import get_logger, Logger
from .decorators import auto_retry
from .service import ScheduledFetcherService
from .service.job import JobLoadInstruction


class ScoreFetcher(ScheduledFetcherService):
    """Periodically fetch and post osu! user scores to leaderboards.

    This service schedules score fetch jobs, listens for new jobs, and collects recent
    scores from the osu! API for each registered user.

    If a user with score fetching disabled decides to enable it at any time, a database
    event is triggered to send a fetch job that will be picked up by this service.

    The scores will get posted to leaderboards if the beatmaps they were performed on
    have eligible leaderboards in the database.
    """

    LOGGER: ClassVar[Logger] = get_logger(__name__, prefix="ScoreFetcher")
    RECORD_MODEL: ClassVar[type[ScoreFetcherTask]] = ScoreFetcherTask
    CHANNEL: ClassVar[str] = ChannelName.SCORE_FETCHER_TASKS
    JOB_NAME: ClassVar[str] = "score-fetch"

    async def _preload_jobs(self):
        """Load enabled score fetch jobs into the scheduler at startup."""
        records = await self._db.get_many(ScoreFetcherTask, enabled=True)
        num_loaded = 0

        for record in records:
            if not record.enabled:
                continue

            instruction = JobLoadInstruction(last_execution=record.last_fetch)
            await self._load_job(record.id, instruction=instruction)
            num_loaded += 1

        self.logger.debug(f"Preloaded jobs: ({num_loaded})")

    @auto_retry(retry_exceptions=(ConnectTimeout,))
    async def _execute_job(self, record_id: int) -> None:
        """Fetch and synchronize a user's recent osu! scores.

        Retrieves score data from the osu! API, checks each score and whether the
        beatmaps the scores were performed on have active leaderboards, then creates and
        posts new Score records accordingly.

        Args:
            record_id:
                ID of the score fetcher record.

        Raises:
            ValueError: If the record does not exist.
        """
        pass  # TODO: Work on scores
        # if not (task := await self._db.get(ScoreFetcherTask, id=task_id)):
        #     raise ValueError(f"Task with ID '{task_id}' not found")
        #
        # user_id = task.user_id
        # await self._respect_rate_limit()
        # scores = await self._oac.get_user_scores(user_id, ScoreType.RECENT)
        #
        # for score in scores:
        #     if not await self._score_is_submittable(score):
        #         continue
        #
        #     _, status_code = await api.scores.post(score, user=PRIMARY_ADMIN_USER_ID)
        #
        #     if status_code == 201:
        #         logger.debug(f"Added score {score["id"]} for user {user_id}")

    async def _score_is_submittable(self, score: dict) -> bool:
        return bool(await self._db.get(Leaderboard, beatmap_id=score["beatmap"]["id"]))
