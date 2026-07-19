from __future__ import annotations

import logging
from typing import ClassVar

from httpx import ConnectTimeout
from structlog.contextvars import bind_contextvars, clear_contextvars

from app.database.enums import RequestStatus
from app.database.models import Request
from app.database.rules.context import ExecutionContext, parse_osu_beatmapset
from app.database.rules.engine.phase2_runner import Phase2Runner
from app.database.rules.exceptions import RuleViolationError
from app.database.rules.registry import get_validator, get_validator_tier
from app.database.rules.validators.metadata import (
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
    _should_reschedule: ClassVar[bool] = False

    async def _resolve_job_instruction(self, record_id: int) -> JobLoadInstruction | None:
        return JobLoadInstruction(execution_time=aware_utcnow())

    @auto_retry(retry_exceptions=(ConnectTimeout,))
    async def _execute_job(self, record_id: int):
        hash_name = Namespace.QUEUE_REQUEST_HANDLER_TASK.hash_name(record_id)
        self.logger.debug(f"Executing RuleValidation job {record_id}, looking up hash={hash_name}")

        try:
            serialized_record = await self._rc.hgetall(hash_name)

            if not serialized_record:
                self.logger.error(
                    f"QueueRequestValidationTask with hashed ID '{record_id}' not found at {hash_name}"
                )
                raise ValueError(f"QueueRequestValidationTask with hashed ID '{record_id}' not found")

            self.logger.debug(
                f"Found serialized validation record for {record_id}: keys={list(serialized_record.keys())}"
            )
            record = QueueRequestValidationTask.deserialize(serialized_record)

            if record.http_request_id:
                bind_contextvars(request_id=record.http_request_id)

            self.logger.debug(
                f"Deserialized validation record: request_id={record.request_id}, "
                f"queue_id={record.queue_id}, beatmapset_id={record.beatmapset_id}"
            )

            try:
                async with OsuAPIClient(self._rc) as osu_client:
                    self.logger.debug(f"Running validation for request {record.request_id}")
                    await self._run_validation(
                        request_id=record.request_id,
                        queue_id=record.queue_id,
                        beatmapset_id=record.beatmapset_id,
                        osu_client=osu_client,
                    )
                    self.logger.debug(f"Validation complete for request {record.request_id}")

                await self._rc.hset(hash_name, "completed_at", aware_utcnow().isoformat())
                self.logger.debug(f"Marked {hash_name} as completed_at")
            finally:
                if record.http_request_id:
                    clear_contextvars()
        except Exception:
            self.logger.exception(f"Failed to execute RuleValidation job {record_id}")
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

            rules = await self._get_active_rules(queue_id, session)

        try:
            beatmapset_dict = await osu_client.get_beatmapset(beatmapset_id)
        except Exception:
            logger.warning(
                f"Failed to fetch beatmapset {beatmapset_id} for request {request_id} validation"
            )
            return

        phase2_rules = [
            r for r in rules
            if get_validator_tier(r.type) == 3
        ]

        if not phase2_rules:
            return

        beatmapset_obj, beatmaps = parse_osu_beatmapset(beatmapset_dict)

        context = ExecutionContext(
            queue_id=queue_id,
            user_id=request.user_id,
            beatmapset=beatmapset_obj,
            beatmaps=beatmaps,
            osu_client=osu_client,
            db=self._db,
            redis=self._rc,
            session=session,
            metadata_providers=_METADATA_PROVIDERS,
        )

        runner = Phase2Runner()
        rejected = await runner.run(phase2_rules, context)

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

    async def _get_active_rules(self, queue_id: int, session) -> list:
        from app.database.crud.rules import RuleCRUD

        crud = RuleCRUD()
        return await crud.get_rules(queue_id, only_active=True, session=session)
