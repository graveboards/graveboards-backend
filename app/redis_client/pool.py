from redis import ConnectionPool

from app.config import REDIS_CONFIGURATION

connection_pool = ConnectionPool(**REDIS_CONFIGURATION)
"""Global shared Redis connection pool.

Used for light workloads requiring a synchronous connection to Redis such as database
events."""
