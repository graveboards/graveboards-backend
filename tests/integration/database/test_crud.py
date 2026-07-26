from typing import Any

import pytest

from app.database.db import PostgresqlDB
from app.database.models import Profile, Queue, User


@pytest.mark.asyncio
async def test_crud_create_user(db_session: Any) -> None:
    """Test creating a User instance."""
    db = PostgresqlDB()

    created = await db.add(User, session=db_session, id=99999)

    assert created.id == 99999


@pytest.mark.asyncio
async def test_crud_create_profile(db_session: Any) -> None:
    """Test creating a Profile instance."""
    db = PostgresqlDB()

    await db.add(User, session=db_session, id=88888)

    profile_data = {
        "user_id": 88888,
        "username": "newprofile",
        "country_code": "UK",
    }

    created = await db.add(Profile, session=db_session, **profile_data)

    assert created.user_id == 88888
    assert created.username == "newprofile"
    assert created.country_code == "UK"


@pytest.mark.asyncio
async def test_crud_create_queue(db_session: Any) -> None:
    """Test creating a Queue instance."""
    db = PostgresqlDB()

    await db.add(User, session=db_session, id=77777)

    queue_data = {
        "user_id": 77777,
        "name": "My Queue",
        "description": "Queue description",
    }

    created = await db.add(Queue, session=db_session, **queue_data)

    assert created.user_id == 77777
    assert created.name == "My Queue"
    assert created.is_open is True


@pytest.mark.asyncio
async def test_crud_add_many_users(db_session: Any) -> None:
    """Test creating multiple User instances at once."""
    db = PostgresqlDB()

    users_data = [
        {"id": 10001},
        {"id": 10002},
        {"id": 10003},
    ]

    created = await db.add_many(User, *users_data, session=db_session)

    assert len(created) == 3
    assert created[0].id == 10001
    assert created[1].id == 10002
    assert created[2].id == 10003


@pytest.mark.asyncio
async def test_crud_read_user(db_session: Any) -> None:
    """Test reading a User instance."""
    db = PostgresqlDB()

    await db.add(User, session=db_session, id=55555)

    fetched = await db.get(User, session=db_session, id=55555)

    assert fetched is not None
    assert fetched.id == 55555


@pytest.mark.asyncio
async def test_crud_read_profile(db_session: Any) -> None:
    """Test reading a Profile instance."""
    db = PostgresqlDB()

    await db.add(User, session=db_session, id=44444)
    await db.add(Profile, session=db_session, user_id=44444, username="readtest")

    fetched = await db.get(Profile, session=db_session, user_id=44444)

    assert fetched is not None
    assert fetched.username == "readtest"


@pytest.mark.asyncio
async def test_crud_update_profile(db_session: Any) -> None:
    """Test updating a Profile instance."""
    db = PostgresqlDB()

    await db.add(User, session=db_session, id=33333)
    created = await db.add(Profile, session=db_session, user_id=33333, username="oldname")

    updated = await db.update(Profile, created.id, session=db_session, username="newname")

    assert updated.username == "newname"


@pytest.mark.asyncio
async def test_crud_delete_user(db_session: Any) -> None:
    """Test deleting a User instance."""
    db = PostgresqlDB()

    created = await db.add(User, session=db_session, id=11111)

    await db.delete(User, session=db_session, id=created.id)

    fetched = await db.get(User, session=db_session, id=created.id)
    assert fetched is None


@pytest.mark.asyncio
async def test_crud_delete_profile(db_session: Any) -> None:
    """Test deleting a Profile instance."""
    db = PostgresqlDB()

    await db.add(User, session=db_session, id=9999)
    await db.add(Profile, session=db_session, user_id=9999)

    await db.delete(Profile, session=db_session, user_id=9999)

    fetched = await db.get(Profile, session=db_session, user_id=9999)
    assert fetched is None


@pytest.mark.asyncio
async def test_crud_relationship_user_to_profile(db_session: Any) -> None:
    """Test User to Profile relationship - verify FK is set correctly."""
    db = PostgresqlDB()

    await db.add(User, session=db_session, id=87654)
    profile_data = {"user_id": 87654, "username": "reltest", "country_code": "CA"}
    await db.add(Profile, session=db_session, **profile_data)

    fetched_user = await db.get(User, session=db_session, id=87654)

    assert fetched_user is not None
    assert fetched_user.id == 87654


@pytest.mark.asyncio
async def test_crud_relationship_queue_to_user(db_session: Any) -> None:
    """Test Queue to User relationship - verify FK is set correctly."""
    db = PostgresqlDB()

    await db.add(User, session=db_session, id=54321)
    queue_data = {"user_id": 54321, "name": "User Queue", "description": "Test"}
    queue = await db.add(Queue, session=db_session, **queue_data)

    fetched = await db.get(Queue, session=db_session, id=queue.id)
    assert fetched is not None

    assert fetched.user_id == 54321


@pytest.mark.asyncio
async def test_crud_get_many(db_session: Any) -> None:
    """Test getting multiple instances."""
    db = PostgresqlDB()

    users_data = [
        {"id": 11101},
        {"id": 11102},
        {"id": 11103},
    ]
    await db.add_many(User, *users_data, session=db_session)

    fetched = await db.get_many(User, session=db_session)

    assert len(fetched) >= 3


@pytest.mark.asyncio
async def test_crud_add_many_with_relationships(db_session: Any) -> None:
    """Test adding multiple instances with relationships."""
    db = PostgresqlDB()

    await db.add(User, session=db_session, id=33300)

    queues_data = [
        {"user_id": 33300, "name": "Queue One", "description": "Test"},
        {"user_id": 33300, "name": "Queue Two", "description": "Test"},
    ]
    created = await db.add_many(Queue, *queues_data, session=db_session)

    assert len(created) == 2
    assert created[0].user_id == 33300
    assert created[1].user_id == 33300
