from typing import ClassVar

from httpx import ConnectTimeout

from app.database.models import ScoreFetcherTask, Leaderboard, BeatmapSnapshot, Score
from app.database.schemas import ScoreSchema
from app.osu_api.enums import ScoreType
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

        Retrieves score data from the osu! API, checks each score against
        eligible leaderboards, and creates Score records directly in the database.

        Args:
            record_id:
                ID of the score fetcher record.

        Raises:
            ValueError: If the record does not exist.
        """
        if not (record := await self._db.get(ScoreFetcherTask, id=record_id)):
            raise ValueError(f"ScoreFetcherTask with ID '{record_id}' not found")

        user_id = record.user_id
        await self._respect_rate_limit()
        scores = await self._oac.get_user_scores(user_id, ScoreType.RECENT)

        leaderboards = await self._db.get_many(
            Leaderboard, _select="beatmap_id"
        )
        eligible_beatmap_ids = {lb.beatmap_id for lb in leaderboards}

        for score in scores:
            try:
                validated_score = ScoreSchema.model_validate(score)
            except Exception:
                continue

            beatmap_id = validated_score.beatmap_id
            if beatmap_id not in eligible_beatmap_ids:
                continue

            leaderboard_id = await self._resolve_leaderboard(beatmap_id)
            if leaderboard_id is None:
                continue

            score_data = validated_score.model_dump()
            score_data["user_id"] = user_id
            score_data["leaderboard_id"] = leaderboard_id

            await self._db.add(Score, **score_data)

    async def _resolve_leaderboard(self, beatmap_id: int) -> int | None:
        """Get the current leaderboard ID for a beatmap."""
        snapshot = await self._db.get(
            BeatmapSnapshot,
            beatmap_id=beatmap_id,
            _sorting=[{"field": "BeatmapSnapshot.id", "order": "desc"}]
        )
        if not snapshot:
            return None
        leaderboard = await self._db.get(
            Leaderboard, beatmap_id=beatmap_id, beatmap_snapshot_id=snapshot.id
        )
        return leaderboard.id if leaderboard else None
