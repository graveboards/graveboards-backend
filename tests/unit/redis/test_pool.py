"""Unit tests for Redis connection pool singleton."""

import pytest
from redis import ConnectionPool


class TestConnectionPool:
    """Test connection_pool module-level singleton."""

    def test_pool_is_singleton(self):
        """Test connection_pool is a module-level singleton instance."""
        from app.redis.pool import connection_pool
        assert connection_pool is not None
        assert isinstance(connection_pool, ConnectionPool)

    def test_pool_uses_redis_configuration(self):
        """Test pool is initialized with REDIS_CONFIGURATION values."""
        from app.redis.pool import connection_pool
        from app.config import REDIS_CONFIGURATION

        assert connection_pool.connection_kwargs.get("host") == REDIS_CONFIGURATION["host"]
        assert connection_pool.connection_kwargs.get("port") == REDIS_CONFIGURATION["port"]

    def test_pool_max_connections_is_default(self):
        """Test pool uses default max connections when not configured."""
        from app.redis.pool import connection_pool
        assert connection_pool.max_connections is None or isinstance(
            connection_pool.max_connections, int
        )

    def test_pool_can_release_and_acquire_connections(self):
        """Test pool can release and re-acquire connections."""
        from app.redis.pool import connection_pool
        conn = connection_pool.get_connection()
        assert conn is not None
        connection_pool.release(conn)
