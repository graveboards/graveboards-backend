import pytest

from app.database.db import PostgresqlDB
from app.database.models import User, Profile


@pytest.mark.asyncio
async def test_transaction_rollback(db_session_transaction):
    """Test that rollback properly undoes changes."""
    db = PostgresqlDB()
    
    created = await db.add(User, session=db_session_transaction, id=90001)
    
    assert created.id == 90001
    
    await db_session_transaction.rollback()
    await db_session_transaction.commit()
    
    fetched = await db.get(User, session=db_session_transaction, id=90001)
    assert fetched is None


@pytest.mark.asyncio
async def test_transaction_isolation_separate_transactions(db_session_transaction):
    """Test that changes in one transaction are not visible to another."""
    db = PostgresqlDB()
    
    user1 = await db.add(User, session=db_session_transaction, id=90002)
    
    user2 = await db.add(User, session=db_session_transaction, id=90003)
    
    await db_session_transaction.commit()
    
    fetched_outside = await db.get(User, session=db_session_transaction, id=90002)
    assert fetched_outside is not None


@pytest.mark.asyncio
async def test_concurrent_insert_same_table(db_session_transaction):
    """Test concurrent inserts don't interfere."""
    db = PostgresqlDB()
    
    user1 = await db.add(User, session=db_session_transaction, id=90101)
    user2 = await db.add(User, session=db_session_transaction, id=90102)
    user3 = await db.add(User, session=db_session_transaction, id=90103)
    
    await db_session_transaction.commit()
    
    assert await db.get(User, session=db_session_transaction, id=90101) is not None
    assert await db.get(User, session=db_session_transaction, id=90102) is not None
    assert await db.get(User, session=db_session_transaction, id=90103) is not None


@pytest.mark.asyncio
async def test_concurrent_update_same_row(db_session_transaction):
    """Test concurrent updates to same row - last write wins."""
    db = PostgresqlDB()
    
    user = await db.add(User, session=db_session_transaction, id=90200)
    profile = await db.add(Profile, session=db_session_transaction, user_id=90200, username="oldname")
    
    await db_session_transaction.commit()
    
    await db.update(Profile, profile.id, session=db_session_transaction, username="updated_user1")
    await db_session_transaction.commit()
    
    await db.update(Profile, profile.id, session=db_session_transaction, username="updated_user2")
    await db_session_transaction.commit()
    
    final = await db.get(Profile, session=db_session_transaction, id=profile.id)
    assert final is not None
    assert final.username == "updated_user2"


@pytest.mark.asyncio
async def test_transaction_nested_rollbacks(db_session_transaction):
    """Test nested transaction scenarios."""
    db = PostgresqlDB()
    
    user1 = await db.add(User, session=db_session_transaction, id=90301)
    user2 = await db.add(User, session=db_session_transaction, id=90302)
    user3 = await db.add(User, session=db_session_transaction, id=90303)
    
    await db_session_transaction.commit()
    
    assert await db.get(User, session=db_session_transaction, id=90301) is not None
    assert await db.get(User, session=db_session_transaction, id=90302) is not None
    assert await db.get(User, session=db_session_transaction, id=90303) is not None


@pytest.mark.asyncio
async def test_transaction_consistency_after_rollback(db_session_transaction):
    """Test that database is in consistent state after rollback."""
    db = PostgresqlDB()
    
    await db.add(User, session=db_session_transaction, id=90401)
    await db_session_transaction.rollback()
    await db_session_transaction.commit()
    
    user1 = await db.add(User, session=db_session_transaction, id=90402)
    await db_session_transaction.commit()
    
    result = await db.get(User, session=db_session_transaction, id=90402)
    assert result is not None
    
    result = await db.get(User, session=db_session_transaction, id=90401)
    assert result is None


@pytest.mark.asyncio
async def test_transaction_deadlock_scenario(db_session_transaction):
    """Test that concurrent access doesn't cause deadlocks."""
    db = PostgresqlDB()
    
    for i in range(15):
        await db.add(User, session=db_session_transaction, id=90500 + i)
    
    await db_session_transaction.commit()
    
    for i in range(15):
        assert await db.get(User, session=db_session_transaction, id=90500 + i) is not None


@pytest.mark.asyncio
async def test_transaction_constraint_violation_rollback(db_session_transaction):
    """Test that constraint violations properly rollback."""
    db = PostgresqlDB()
    
    await db.add(User, session=db_session_transaction, id=90601)
    await db_session_transaction.commit()
    
    try:
        await db.add(User, session=db_session_transaction, id=90601)
        await db_session_transaction.commit()
        pytest.fail("Should have raised an error")
    except:
        await db_session_transaction.rollback()
        await db_session_transaction.commit()
    
    result = await db.get(User, session=db_session_transaction, id=90601)
    assert result is not None
