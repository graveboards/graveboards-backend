from sqlalchemy import event
from sqlalchemy.orm.attributes import AttributeEventToken

from app.logging import get_logger
from app.redis import redis_connection, ChannelName
from app.database.models import ScoreFetcherTask

__all__ = [
    "score_fetcher_task_enabled_set"
]

logger = get_logger(__name__)


@event.listens_for(ScoreFetcherTask.enabled, "set")
def score_fetcher_task_enabled_set(target: ScoreFetcherTask, value: bool, oldvalue: bool, initiator: AttributeEventToken):
    """Publish ``ScoreFetcherTask`` activation events to Redis.

    When the ``enabled`` attribute transitions to True, the task ID is published to a
    Redis channel for distributed worker pickup.

    Args:
        target:
            The ``ScoreFetcherTask`` instance being modified.
        value:
            The new boolean value.
        oldvalue:
            The previous boolean value.
        initiator:
            SQLAlchemy attribute event metadata.

    Side Effects:
        Publishes task ID to Redis.
    """
    if value:
        with redis_connection() as rc:
            rc.publish(ChannelName.SCORE_FETCHER_TASKS.value, target.id)
            logger.debug(f"Published ScoreFetcherTask ID to redis channel '{ChannelName.SCORE_FETCHER_TASKS.value}': {target.id}")
