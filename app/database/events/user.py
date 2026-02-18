from sqlalchemy import event
from sqlalchemy.engine.base import Connection
from sqlalchemy.sql import insert
from sqlalchemy.orm.mapper import Mapper

from app.logging import get_logger
from app.redis import redis_connection, ChannelName
from app.database.models import User, ScoreFetcherTask, ProfileFetcherTask

__all__ = [
    "user_after_insert"
]

logger = get_logger(__name__)


@event.listens_for(User, "after_insert")
def user_after_insert(mapper: Mapper[User], connection: Connection, target: User):
    """Initialize background tasks for a newly created ``User``.

    Automatically creates:
        - A ``ScoreFetcherTask``
        - A ``ProfileFetcherTask``

    The ``ProfileFetcherTask`` ID is immediately published to Redis to trigger
    asynchronous processing.

    Args:
        mapper:
            SQLAlchemy mapper for ``User``.
        connection:
            Active database connection.
        target:
            The newly inserted ``User``.

    Side Effects:
        Inserts task rows.
        Publishes ``ProfileFetcherTask`` ID to Redis.
    """
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
