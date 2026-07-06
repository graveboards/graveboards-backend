"""Integration tests for Redis cache operations.

These tests require a running Redis instance (e.g. via docker-compose).
They are marked with @pytest.mark.integration and will be skipped if
REDIS_TEST_URL is not set or Redis is unreachable.
"""

import pytest
import asyncio

from app.redis.models import Beatmap, Beatmapset, OsuClientOAuthToken, QueueRequestHandlerTask


pytestmark = pytest.mark.integration


def require_redis(func):
    """Skip test if REDIS_TEST_URL environment variable is not set."""
    import os
    return pytest.mark.skipif(
        not os.environ.get("REDIS_TEST_URL"),
        reason="REDIS_TEST_URL not set — skipping Redis integration test"
    )(func)


def get_redis_client():
    """Create a RedisClient connected to the test Redis instance."""
    import os
    from app.redis.rc import RedisClient

    url = os.environ["REDIS_TEST_URL"]
    rc = RedisClient.__new__(RedisClient)
    rc.host = url.replace("redis://", "").split("/")[0].split(":")[0]
    port_part = url.replace("redis://", "").split("/")[0].split(":")
    rc.port = int(port_part[1]) if len(port_part) > 1 else 6379
    rc.db = int(url.split("/")[-1]) if "/" in url else 0
    rc.password = None
    return rc


class TestRedisCacheIntegration:
    """Integration tests for Redis cache operations."""

    @require_redis
    @pytest.mark.asyncio
    async def test_cache_beatmap_roundtrip(self):
        """Test caching and retrieving a beatmap via Redis."""
        rc = get_redis_client()
        try:
            beatmap = Beatmap(
                id=999999, user_id=67890, beatmapset_id=11111,
                version="Test", creator="Test", bpm=180.0,
                total_length=240, hit_length=216, status="ranked",
                difficulty_rating=7.5, playcount=5000, passcount=3000,
                mode="osu", mode_int=0, accuracy=95.5, ar=8.0, cs=4.0,
                drain=6.0, count_circles=200, count_sliders=100,
                count_spinners=5, max_combo=1500, is_scoreable=True,
                ranked=1, url="https://example.com", checksum="abc",
                failtimes={"exit": [], "fail": []},
                last_updated="2024-06-15T12:00:00+00:00",
                deleted_at=None, owners=[], top_tag_ids=[],
            )
            serialized = beatmap.serialize()
            key = f"test:beatmap:{beatmap.id}"

            await rc.hset(key, mapping=serialized)
            stored = await rc.hgetall(key)

            assert stored is not None
            assert stored["id"] == "999999"
            assert stored["version"] == "Test"

            restored = Beatmap.deserialize(stored)
            assert restored.id == 999999
            assert restored.bpm == 180.0

            await rc.delete(key)
        finally:
            await rc.close()

    @require_redis
    @pytest.mark.asyncio
    async def test_cache_expiry(self):
        """Test cached items expire after TTL."""
        rc = get_redis_client()
        try:
            key = "test:expiry"
            await rc.set(key, "value", ex=1)

            stored = await rc.get(key)
            assert stored == "value"

            await asyncio.sleep(1.5)
            expired = await rc.get(key)
            assert expired is None
        finally:
            await rc.close()

    @require_redis
    @pytest.mark.asyncio
    async def test_cache_delete(self):
        """Test deleting a cached item."""
        rc = get_redis_client()
        try:
            key = "test:delete"
            await rc.set(key, "value")
            assert await rc.get(key) == "value"

            deleted = await rc.delete(key)
            assert deleted == 1
            assert await rc.get(key) is None
        finally:
            await rc.close()

    @require_redis
    @pytest.mark.asyncio
    async def test_oauth_token_roundtrip(self):
        """Test OAuth token cache round-trip."""
        rc = get_redis_client()
        try:
            token = OsuClientOAuthToken(
                access_token="test_token_abc", token_type="bearer",
                expires_in=5184000, expires_at=1735689600,
            )
            serialized = token.serialize()
            key = "test:oauth:test_user"

            await rc.set(key, str(serialized))
            stored_raw = await rc.get(key)
            assert stored_raw is not None

            import ast
            stored = ast.literal_eval(stored_raw)
            restored = OsuClientOAuthToken.deserialize(stored)
            assert restored.access_token == "test_token_abc"
            assert restored.expires_in == 5184000

            await rc.delete(key)
        finally:
            await rc.close()

    @require_redis
    @pytest.mark.asyncio
    async def test_task_roundtrip(self):
        """Test task cache round-trip."""
        rc = get_redis_client()
        try:
            task = QueueRequestHandlerTask(
                user_id=12345678, beatmapset_id=35965, queue_id=1,
                comment="Test comment", mv_checked=False,
            )
            serialized = task.serialize()
            key = f"test:task:{task.hashed_id}"

            await rc.hset(key, mapping=serialized)
            stored = await rc.hgetall(key)

            assert stored is not None
            assert stored["user_id"] == "12345678"
            assert stored["comment"] == "Test comment"

            restored = QueueRequestHandlerTask.deserialize(stored)
            assert restored.user_id == 12345678
            assert restored.beatmapset_id == 35965
            assert restored.mv_checked is False

            await rc.delete(key)
        finally:
            await rc.close()
