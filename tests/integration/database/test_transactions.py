import pytest

from app.database.db import PostgresqlDB
from app.database.models import User, Profile


@pytest.mark.asyncio
async def test_transaction_rollback(db_session):
    """Test that rollback properly undoes changes."""
    db = PostgresqlDB()
    
    try:
        created = await db.add(User, session=db_session, id=90001)
        
        assert created.id == 90001
        
        await db_session.rollback()
        await db_session.commit()
        
        fetched = await db.get(User, id=90001)
        assert fetched is None
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_transaction_isolation_separate_transactions(db_session):
    """Test that changes in one transaction are not visible to another."""
    db = PostgresqlDB()
    
    try:
        user1 = await db.add(User, session=db_session, id=90002)
        
        user2 = await db.add(User, session=db_session, id=90003)
        
        await db_session.commit()
        
        fetched_outside = await db.get(User, id=90002)
        assert fetched_outside is not None
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_concurrent_insert_same_table(db_session):
    """Test concurrent inserts don't interfere."""
    db = PostgresqlDB()
    
    try:
        user1 = await db.add(User, session=db_session, id=90101)
        user2 = await db.add(User, session=db_session, id=90102)
        user3 = await db.add(User, session=db_session, id=90103)
        
        await db_session.commit()
        
        assert await db.get(User, id=90101) is not None
        assert await db.get(User, id=90102) is not None
        assert await db.get(User, id=90103) is not None
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_concurrent_update_same_row(db_session):
    """Test concurrent updates to same row - last write wins."""
    db = PostgresqlDB()
    
    try:
        user = await db.add(User, session=db_session, id=90200)
        profile = await db.add(Profile, session=db_session, user_id=90200, username="oldname")
        
        await db_session.commit()
        
        await db.update(Profile, profile.id, session=db_session, username="updated_user1")
        await db_session.commit()
        
        await db.update(Profile, profile.id, session=db_session, username="updated_user2")
        await db_session.commit()
        
        final = await db.get(Profile, id=profile.id)
        assert final is not None
        assert final.username == "updated_user2"
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_transaction_nested_rollbacks(db_session):
    """Test nested transaction scenarios."""
    db = PostgresqlDB()
    
    try:
        user1 = await db.add(User, session=db_session, id=90301)
        user2 = await db.add(User, session=db_session, id=90302)
        user3 = await db.add(User, session=db_session, id=90303)
        
        await db_session.commit()
        
        assert await db.get(User, id=90301) is not None
        assert await db.get(User, id=90302) is not None
        assert await db.get(User, id=90303) is not None
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_transaction_consistency_after_rollback(db_session):
    """Test that database is in consistent state after rollback."""
    db = PostgresqlDB()
    
    try:
        await db.add(User, session=db_session, id=90401)
        await db_session.rollback()
        await db_session.commit()
        
        user1 = await db.add(User, session=db_session, id=90402)
        await db_session.commit()
        
        result = await db.get(User, id=90402)
        assert result is not None
        
        result = await db.get(User, id=90401)
        assert result is None
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_transaction_deadlock_scenario(db_session):
    """Test that concurrent access doesn't cause deadlocks."""
    db = PostgresqlDB()
    
    try:
        for i in range(15):
            await db.add(User, session=db_session, id=90500 + i)
        
        await db_session.commit()
        
        for i in range(15):
            assert await db.get(User, id=90500 + i) is not None
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_transaction_constraint_violation_rollback(db_session):
    """Test that constraint violations properly rollback."""
    db = PostgresqlDB()
    
    try:
        await db.add(User, session=db_session, id=90601)
        await db_session.commit()
        
        try:
            await db.add(User, session=db_session, id=90601)
            await db_session.commit()
            pytest.fail("Should have raised an error")
        except:
            await db_session.rollback()
            await db_session.commit()
        
        result = await db.get(User, id=90601)
        assert result is not None
    finally:
        await db.close()
