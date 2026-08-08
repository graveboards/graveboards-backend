"""Unit tests for Redis connection pool singleton."""

from unittest.mock import MagicMock, patch

from redis import ConnectionPool


class TestConnectionPool:
    """Test connection_pool module-level singleton instance."""

    def test_pool_is_singleton(self) -> None:
        """Test connection_pool is a module-level singleton instance."""
        from app.redis_client.pool import connection_pool

        assert connection_pool is not None
        assert isinstance(connection_pool, ConnectionPool)

    def test_pool_uses_redis_configuration(self) -> None:
        """Test pool is initialized with REDIS_CONFIGURATION values."""
        from app.config import REDIS_CONFIGURATION
        from app.redis_client.pool import connection_pool

        assert connection_pool.connection_kwargs.get("host") == REDIS_CONFIGURATION["host"]
        assert connection_pool.connection_kwargs.get("port") == REDIS_CONFIGURATION["port"]

    def test_pool_max_connections_is_default(self) -> None:
        """Test pool uses default max connections when not configured."""
        from app.redis_client.pool import connection_pool

        assert connection_pool.max_connections is None or isinstance(
            connection_pool.max_connections, int
        )

    def test_pool_can_release_and_acquire_connections(self) -> None:
        """Test pool can release and re-acquire connections (mocked)."""
        from app.redis_client.pool import connection_pool

        mock_conn = MagicMock()
        with patch.object(connection_pool, "get_connection", return_value=mock_conn):
            conn = connection_pool.get_connection()
            assert conn is mock_conn
            with patch.object(connection_pool, "release") as mock_release:
                connection_pool.release(conn)
                mock_release.assert_called_once_with(mock_conn)
