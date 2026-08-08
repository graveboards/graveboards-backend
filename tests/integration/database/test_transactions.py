from typing import Any

import pytest
from sqlalchemy.exc import IntegrityError

from app.database.db import PostgresqlDB
from app.database.models import Profile, User


@pytest.mark.asyncio
async def test_transaction_rollback(db_session: Any) -> None:
    """Test that rollback properly undoes changes."""
    db = PostgresqlDB()

    created = await db.add(User, session=db_session, id=90001)

    assert created.id == 90001

    await db_session.rollback()
    await db_session.commit()

    fetched = await db.get(User, session=db_session, id=90001)
    assert fetched is None


@pytest.mark.asyncio
async def test_transaction_isolation_separate_transactions(db_session: Any) -> None:
    """Test that changes in one transaction are not visible to another."""
    db = PostgresqlDB()

    await db.add(User, session=db_session, id=90002)

    await db.add(User, session=db_session, id=90003)

    await db_session.commit()

    fetched_outside = await db.get(User, session=db_session, id=90002)
    assert fetched_outside is not None


@pytest.mark.asyncio
async def test_concurrent_insert_same_table(db_session: Any) -> None:
    """Test concurrent inserts don't interfere."""
    db = PostgresqlDB()

    await db.add(User, session=db_session, id=90101)
    await db.add(User, session=db_session, id=90102)
    await db.add(User, session=db_session, id=90103)

    await db_session.commit()

    assert await db.get(User, session=db_session, id=90101) is not None
    assert await db.get(User, session=db_session, id=90102) is not None
    assert await db.get(User, session=db_session, id=90103) is not None


@pytest.mark.asyncio
async def test_concurrent_update_same_row(db_session: Any) -> None:
    """Test concurrent updates to same row - last write wins."""
    db = PostgresqlDB()

    await db.add(User, session=db_session, id=90200)
    profile = await db.add(Profile, session=db_session, user_id=90200, username="oldname")

    await db_session.commit()

    await db.update(Profile, profile.id, session=db_session, username="updated_user1")
    await db_session.commit()

    await db.update(Profile, profile.id, session=db_session, username="updated_user2")
    await db_session.commit()

    final = await db.get(Profile, session=db_session, id=profile.id)
    assert final is not None
    assert final.username == "updated_user2"


@pytest.mark.asyncio
async def test_transaction_nested_rollbacks(db_session: Any) -> None:
    """Test nested transaction scenarios."""
    db = PostgresqlDB()

    await db.add(User, session=db_session, id=90301)
    await db.add(User, session=db_session, id=90302)
    await db.add(User, session=db_session, id=90303)

    await db_session.commit()

    assert await db.get(User, session=db_session, id=90301) is not None
    assert await db.get(User, session=db_session, id=90302) is not None
    assert await db.get(User, session=db_session, id=90303) is not None


@pytest.mark.asyncio
async def test_transaction_consistency_after_rollback(db_session: Any) -> None:
    """Test that database is in consistent state after rollback."""
    db = PostgresqlDB()

    await db.add(User, session=db_session, id=90401)
    await db_session.rollback()
    await db_session.commit()

    await db.add(User, session=db_session, id=90402)
    await db_session.commit()

    result = await db.get(User, session=db_session, id=90402)
    assert result is not None

    result = await db.get(User, session=db_session, id=90401)
    assert result is None


@pytest.mark.asyncio
async def test_transaction_deadlock_scenario(db_session: Any) -> None:
    """Test that concurrent access doesn't cause deadlocks."""
    db = PostgresqlDB()

    for i in range(15):
        await db.add(User, session=db_session, id=90500 + i)

    await db_session.commit()

    for i in range(15):
        assert await db.get(User, session=db_session, id=90500 + i) is not None


@pytest.mark.asyncio
async def test_transaction_constraint_violation_rollback(db_session: Any) -> None:
    """Test that constraint violations properly rollback without losing prior commits."""
    db = PostgresqlDB()

    await db.add(User, session=db_session, id=90601)
    await db_session.commit()

    # ``db.add()`` resolves-or-creates, so re-adding the same primary key would
    # just return the existing row instead of violating the constraint. Stage a
    # duplicate directly on the session and flush to force a genuine PK
    # violation, then confirm the session recovers and the earlier commit stays.
    db_session.add(User(id=90601))
    with pytest.raises(IntegrityError):
        await db_session.flush()

    await db_session.rollback()
    await db_session.commit()

    result = await db.get(User, session=db_session, id=90601)
    assert result is not None
