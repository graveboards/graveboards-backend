from __future__ import annotations

import logging
from typing import ClassVar

from httpx import ConnectTimeout

from app.database.enums import RequestStatus
from app.database.models import Request
from app.database.restrictions.context import ExecutionContext
from app.database.restrictions.engine.phase2_runner import Phase2Runner
from app.database.restrictions.exceptions import RestrictionViolationError
from app.database.restrictions.registry import get_validator, get_validator_tier
from app.database.restrictions.validators.metadata import (
    SongIdentityProvider,
    BeatmapStatsProvider,
    CreatorIdentityProvider,
    DurationProvider,
)
from app.osu_api.client import OsuAPIClient
from app.redis import ChannelName, Namespace
from app.redis.models import QueueRequestValidationTask
from app.utils import aware_utcnow
from app.logging import get_logger, Logger
from .decorators import auto_retry
from .service import ScheduledService
from .service.job import JobLoadInstruction

logger = get_logger(__name__)

_METADATA_PROVIDERS = {
    "song_identity": SongIdentityProvider,
    "beatmap_stats": BeatmapStatsProvider,
    "creator_identity": CreatorIdentityProvider,
    "duration": DurationProvider,
}


class RuleValidationService(ScheduledService):
    """Processes Tier 3 rule validations asynchronously.

    This service listens for validation tasks published to Redis and runs
    Tier 3 validators (osu! API backed) against the associated request.
    If a validator rejects the request, the request status is updated to
    REJECTED and the rejection reason is stored.
    """

    LOGGER: ClassVar[Logger] = get_logger(__name__, prefix="RuleValidationService")
    CHANNEL: ClassVar[str] = ChannelName.QUEUE_REQUEST_VALIDATION_TASKS
    JOB_NAME: ClassVar[str] = "rule-validation"

    async def _resolve_job_instruction(self, record_id: int) -> JobLoadInstruction | None:
        return JobLoadInstruction(execution_time=aware_utcnow())

    @auto_retry(retry_exceptions=(ConnectTimeout,))
    async def _execute_job(self, record_id: int):
        hash_name = Namespace.QUEUE_REQUEST_HANDLER_TASK.hash_name(record_id)

        try:
            serialized_record = await self._rc.hgetall(hash_name)

            if not serialized_record:
                raise ValueError(f"QueueRequestValidationTask with hashed ID '{record_id}' not found")

            record = QueueRequestValidationTask.deserialize(serialized_record)

            async with OsuAPIClient(self._rc) as osu_client:
                await self._run_validation(
                    request_id=record.request_id,
                    queue_id=record.queue_id,
                    beatmapset_id=record.beatmapset_id,
                    osu_client=osu_client,
                )

            await self._rc.hset(hash_name, "completed_at", aware_utcnow().isoformat())
        except Exception:
            await self._rc.hset(hash_name, "failed_at", aware_utcnow().isoformat())
            raise

    async def _run_validation(
        self,
        request_id: int,
        queue_id: int,
        beatmapset_id: int,
        osu_client: OsuAPIClient,
    ) -> None:
        async with self._db.session() as session:
            request = await self._db.get(Request, id=request_id, session=session)

            if not request:
                logger.warning(f"Request {request_id} not found for validation")
                return

            restrictions = await self._get_active_restrictions(queue_id, session)

        try:
            beatmapset_dict = await osu_client.get_beatmapset(beatmapset_id)
        except Exception:
            logger.warning(
                f"Failed to fetch beatmapset {beatmapset_id} for request {request_id} validation"
            )
            return

        phase2_restrictions = [
            r for r in restrictions
            if get_validator_tier(r.restriction_type) == 3
        ]

        if not phase2_restrictions:
            return

        context = ExecutionContext(
            queue_id=queue_id,
            user_id=request.user_id,
            beatmapset=beatmapset_dict,
            osu_client=osu_client,
            db=self._db,
            redis=self._rc,
            session=session,
            metadata_providers=_METADATA_PROVIDERS,
        )

        runner = Phase2Runner()
        rejected = await runner.run(phase2_restrictions, context)

        if rejected:
            rejection_reason = f"Rejected by rule engine: {', '.join(rejected)}"
            await self._db.update(
                Request,
                request_id,
                status=RequestStatus.REJECTED,
                rejection_reason=rejection_reason,
            )
            logger.info(
                f"Request {request_id} rejected by Phase 2 validators: {rejected}"
            )

    async def _get_active_restrictions(self, queue_id: int, session) -> list:
        from app.database.crud.restrictions import RestrictionCRUD

        crud = RestrictionCRUD()
        return await crud.get_restrictions(queue_id, only_active=True, session=session)
