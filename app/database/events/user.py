import logging

from sqlalchemy import event
from sqlalchemy.engine.base import Connection
from sqlalchemy.sql import insert
from sqlalchemy.orm.mapper import Mapper

from app.database.models import User, ScoreFetcherTask, ProfileFetcherTask
from app.redis import redis_connection, ChannelName

__all__ = [
    "user_after_insert"
]

logger = logging.getLogger(__name__)


@event.listens_for(User, "after_insert")
def user_after_insert(mapper: Mapper[User], connection: Connection, target: User):
    info = {"id": target.id}
    logger.debug(f"New User detected (after_insert): {info}")

    insert_score_fetcher_task_stmt = (
        insert(ScoreFetcherTask)
        .values(user_id=target.id)
    )
    insert_profile_fetcher_task_stmt = (
        insert(ProfileFetcherTask)
        .values(user_id=target.id)
        .returning(ProfileFetcherTask.id)
    )

    connection.execute(insert_score_fetcher_task_stmt)
    insert_profile_fetcher_result = connection.execute(insert_profile_fetcher_task_stmt)
    profile_fetcher_task_id = insert_profile_fetcher_result.scalar()
    logger.debug(f"Inserted new ScoreFetcherTask and ProfileFetcherTask with user_id={target.id}")

    with redis_connection() as rc:
        rc.publish(ChannelName.PROFILE_FETCHER_TASKS.value, profile_fetcher_task_id)
        logger.debug(f"Published ProfileFetcherTask ID to redis channel '{ChannelName.PROFILE_FETCHER_TASKS.value}': {profile_fetcher_task_id}")
