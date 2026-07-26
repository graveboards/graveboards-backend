from typing import Any

import pytest

from app.database.db import PostgresqlDB
from app.database.models import Profile, Queue, User


@pytest.fixture
def db() -> PostgresqlDB:
    return PostgresqlDB()


@pytest.mark.asyncio
async def test_resolve_or_create_pk_lookup_existing(db: PostgresqlDB, db_session: Any) -> None:
    """PK lookup: existing user by id should resolve to same instance."""
    user = await db.add(User, session=db_session, id=100001)

    resolved = await db.add(User, session=db_session, id=100001)

    assert resolved.id == 100001
    assert resolved is user


@pytest.mark.asyncio
async def test_resolve_or_create_pk_lookup_new(db: PostgresqlDB, db_session: Any) -> None:
    """PK lookup: new user with given id should create."""
    created = await db.add(User, session=db_session, id=100002)

    assert created.id == 100002


@pytest.mark.asyncio
async def test_resolve_or_create_unique_column_existing(db: PostgresqlDB, db_session: Any) -> None:
    """Unique column lookup: existing profile by unique user_id should resolve."""
    await db.add(User, session=db_session, id=100003)
    profile = await db.add(Profile, session=db_session, user_id=100003, username="original")

    resolved = await db.add(Profile, session=db_session, user_id=100003, username="different")

    assert resolved.id == profile.id
    assert resolved.username == "original"
    assert resolved is profile


@pytest.mark.asyncio
async def test_resolve_or_create_unique_column_new(db: PostgresqlDB, db_session: Any) -> None:
    """Unique column lookup: new profile by unique user_id should create."""
    await db.add(User, session=db_session, id=100004)

    created = await db.add(Profile, session=db_session, user_id=100004, username="newprofile")

    assert created.user_id == 100004
    assert created.username == "newprofile"


@pytest.mark.asyncio
async def test_resolve_or_create_composite_unique_existing(
    db: PostgresqlDB, db_session: Any
) -> None:
    """Composite unique constraint: existing queue by (user_id, name) should resolve."""
    await db.add(User, session=db_session, id=100005)
    queue = await db.add(
        Queue, session=db_session, user_id=100005, name="MyQueue", description="desc"
    )

    resolved = await db.add(
        Queue, session=db_session, user_id=100005, name="MyQueue", description="different desc"
    )

    assert resolved.id == queue.id
    assert resolved.description == "desc"
    assert resolved is queue


@pytest.mark.asyncio
async def test_resolve_or_create_composite_unique_new_same_user(
    db: PostgresqlDB, db_session: Any
) -> None:
    """Composite unique constraint: new queue with same user_id but different name should create."""
    await db.add(User, session=db_session, id=100006)

    q1 = await db.add(Queue, session=db_session, user_id=100006, name="QueueA", description="desc")
    q2 = await db.add(Queue, session=db_session, user_id=100006, name="QueueB", description="desc")

    assert q1.id != q2.id
    assert q1.name == "QueueA"
    assert q2.name == "QueueB"


@pytest.mark.asyncio
async def test_resolve_or_create_cross_session_resolve(db: PostgresqlDB, db_session: Any) -> None:
    """Cross-session: object exists in DB but not in identity map should still resolve via DB query.

    This is the key scenario that the identity map scan was handling but is now handled
    by the database query. The old identity map scan would NOT find objects from a
    different session, so it would fall through to the DB query anyway. This test
    verifies that behavior is preserved.
    """
    async with db.session() as session1:
        await db.add(User, session=session1, id=100007)
        await db.add(Profile, session=session1, user_id=100007, username="crosssession")

    async with db.session() as session2:
        resolved = await db.add(
            Profile, session=session2, user_id=100007, username="should_resolve"
        )

        assert resolved.user_id == 100007
        assert resolved.username == "crosssession"

        fetched = await db.get(Profile, session=session2, user_id=100007)

        assert fetched is not None
        assert fetched.username == "crosssession"


@pytest.mark.asyncio
async def test_resolve_or_create_relationship_scalar(db: PostgresqlDB, db_session: Any) -> None:
    """Relationship: creating user with nested profile should resolve profile by unique user_id."""
    created = await db.add(
        User,
        session=db_session,
        id=100009,
        profile={"user_id": 100009, "username": "withprofile", "country_code": "US"},
    )

    assert created.id == 100009

    profile = await db.get(Profile, session=db_session, user_id=100009)
    assert profile is not None
    assert profile.username == "withprofile"
    assert profile.country_code == "US"


@pytest.mark.asyncio
async def test_resolve_or_create_relationship_scalar_resolve_existing(
    db: PostgresqlDB, db_session: Any
) -> None:
    """Relationship: existing profile should be resolved, not duplicated."""
    await db.add(User, session=db_session, id=100010)
    await db.add(Profile, session=db_session, user_id=100010, username="existing")

    await db.add(
        User,
        session=db_session,
        id=100010,
        profile={"user_id": 100010, "username": "should_not_change"},
    )

    profile = await db.get(Profile, session=db_session, user_id=100010)
    assert profile is not None
    assert profile.username == "existing"


@pytest.mark.asyncio
async def test_resolve_or_create_relationship_list(db: PostgresqlDB, db_session: Any) -> None:
    """Relationship: creating user with multiple queues should create all."""
    created = await db.add(
        User,
        session=db_session,
        id=100011,
        queues=[
            {"user_id": 100011, "name": "Q1", "description": "first"},
            {"user_id": 100011, "name": "Q2", "description": "second"},
        ],
    )

    assert created.id == 100011

    queues_result = await db.get_many(Queue, session=db_session, user_id=100011)
    queues = queues_result if isinstance(queues_result, list) else queues_result[0]
    assert len(queues) == 2
    names = {q.name for q in queues}
    assert names == {"Q1", "Q2"}


@pytest.mark.asyncio
async def test_resolve_or_create_relationship_list_resolve_existing(
    db: PostgresqlDB, db_session: Any
) -> None:
    """Relationship: existing queue with same (user_id, name) should be resolved, new one created."""
    await db.add(User, session=db_session, id=100012)

    await db.add(
        User,
        session=db_session,
        id=100012,
        queues=[
            {"user_id": 100012, "name": "QueueA", "description": "first"},
            {"user_id": 100012, "name": "QueueB", "description": "second"},
        ],
    )

    queues_result = await db.get_many(Queue, session=db_session, user_id=100012)
    queues = queues_result if isinstance(queues_result, list) else queues_result[0]
    assert len(queues) == 2
    names = {q.name for q in queues}
    assert names == {"QueueA", "QueueB"}

    await db.add(
        User,
        session=db_session,
        id=100012,
        queues=[
            {"user_id": 100012, "name": "QueueA", "description": "should_resolve"},
            {"user_id": 100012, "name": "QueueC", "description": "should_create"},
        ],
    )

    queues_result = await db.get_many(Queue, session=db_session, user_id=100012)
    queues = queues_result if isinstance(queues_result, list) else queues_result[0]
    names = {q.name for q in queues}
    assert "QueueA" in names
    assert "QueueC" in names


@pytest.mark.asyncio
async def test_resolve_or_create_no_match_creates(db: PostgresqlDB, db_session: Any) -> None:
    """No unique match: should create a new instance."""
    created = await db.add(User, session=db_session, id=100013)

    assert created.id == 100013


@pytest.mark.asyncio
async def test_resolve_or_create_multiple_unique_columns(db: PostgresqlDB, db_session: Any) -> None:
    """Model with multiple unique constraints: all should be checked."""
    await db.add(User, session=db_session, id=100014)

    p1 = await db.add(Profile, session=db_session, user_id=100014, username="unique1")

    resolved = await db.add(Profile, session=db_session, user_id=100014, username="different1")

    assert resolved.id == p1.id
    assert resolved.username == "unique1"


@pytest.mark.asyncio
async def test_resolve_or_create_add_many_resolves(db: PostgresqlDB, db_session: Any) -> None:
    """add_many: existing users should be resolved, not duplicated."""
    await db.add(User, session=db_session, id=100015)
    await db.add(User, session=db_session, id=100016)

    created = await db.add_many(
        User,
        {"id": 100015},
        {"id": 100016},
        {"id": 100017},
        session=db_session,
    )

    assert len(created) == 3
    ids = {u.id for u in created}
    assert ids == {100015, 100016, 100017}


@pytest.mark.asyncio
async def test_resolve_or_create_unique_constraint_then_different(
    db: PostgresqlDB, db_session: Any
) -> None:
    """Composite unique: same user_id but different name creates separate queues."""
    await db.add(User, session=db_session, id=100018)

    queues = await db.add_many(
        Queue,
        {"user_id": 100018, "name": "Alpha", "description": "first"},
        {"user_id": 100018, "name": "Beta", "description": "second"},
        {"user_id": 100018, "name": "Gamma", "description": "third"},
        session=db_session,
    )

    assert len(queues) == 3
    names = {q.name for q in queues}
    assert names == {"Alpha", "Beta", "Gamma"}

    resolved = await db.add(
        Queue,
        session=db_session,
        user_id=100018,
        name="Alpha",
        description="resolved",
    )

    assert resolved.name == "Alpha"
    assert resolved.description == "first"
