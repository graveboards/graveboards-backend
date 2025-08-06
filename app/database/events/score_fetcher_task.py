from sqlalchemy import event
from sqlalchemy.orm.attributes import AttributeEventToken

from app.database.models import ScoreFetcherTask
from app.redis import redis_connection, ChannelName

__all__ = [
    "score_fetcher_task_enabled_set"
]


@event.listens_for(ScoreFetcherTask.enabled, "set")
def score_fetcher_task_enabled_set(target: ScoreFetcherTask, value: bool, oldvalue: bool, initiator: AttributeEventToken):
    if value:
        with redis_connection() as rc:
            rc.publish(ChannelName.SCORE_FETCHER_TASKS.value, target.id)
