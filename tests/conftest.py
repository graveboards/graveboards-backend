import asyncio

import pytest

import asyncpg
import redis

from app.config import POSTGRESQL_CONFIGURATION, REDIS_CONFIGURATION


@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop


@pytest.fixture(scope="session")
async def test_db_pool():
    pool = await asyncpg.create_pool(
        host=POSTGRESQL_CONFIGURATION["host"],
        port=POSTGRESQL_CONFIGURATION["port"],
        user=POSTGRESQL_CONFIGURATION["username"],
        password=POSTGRESQL_CONFIGURATION["password"],
        database=POSTGRESQL_CONFIGURATION["database"],
    )
    yield pool
    await pool.close()


@pytest.fixture(scope="function")
async def db_transaction(test_db_pool):
    conn = await test_db_pool.acquire()
    tx = conn.transaction()
    await tx.start()
    try:
        yield conn
    finally:
        await tx.rollback()
        await test_db_pool.release(conn)


@pytest.fixture(scope="function")
async def clean_redis():
    r = redis.Redis(
        host=REDIS_CONFIGURATION["host"],
        port=REDIS_CONFIGURATION["port"],
        db=REDIS_CONFIGURATION["db"],
        decode_responses=REDIS_CONFIGURATION["decode_responses"],
    )
    r.flushdb()
    yield r
    r.flushdb()
