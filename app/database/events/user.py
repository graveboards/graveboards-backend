from sqlalchemy import event
from sqlalchemy.engine.base import Connection
from sqlalchemy.sql import insert
from sqlalchemy.orm.mapper import Mapper

from app.database.models import User, ScoreFetcherTask, ProfileFetcherTask
from app.redis import redis_connection, ChannelName

__all__ = [
    "user_after_insert"
]


@event.listens_for(User, "after_insert")
def user_after_insert(mapper: Mapper[User], connection: Connection, target: User):
    insert_score_fetcher_stmt = (
        insert(ScoreFetcherTask)
        .values(user_id=target.id)
    )
    insert_profile_fetcher_stmt = (
        insert(ProfileFetcherTask)
        .values(user_id=target.id)
        .returning(ProfileFetcherTask.id)
    )

    connection.execute(insert_score_fetcher_stmt)
    result = connection.execute(insert_profile_fetcher_stmt)
    profile_fetcher_task_id = result.scalar()

    with redis_connection() as rc:
        rc.publish(ChannelName.PROFILE_FETCHER_TASKS.value, profile_fetcher_task_id)
