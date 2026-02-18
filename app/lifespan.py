import asyncio
from contextlib import asynccontextmanager

from connexion.middleware import ConnexionMiddleware

from .redis import RedisClient
from .database import PostgresqlDB
from .config import DISABLE_SECURITY
from .logging import setup_logging, get_logger
from .daemon import Daemon
from .setup import setup


@asynccontextmanager
async def lifespan(app: ConnexionMiddleware):
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Start of app lifespan")

    await setup()

    if DISABLE_SECURITY:
        logger.warning("Security has been disabled!")

    rc = RedisClient()
    db = PostgresqlDB()

    daemon_app = Daemon(rc, db)
    await daemon_app.start()
    daemon_task = asyncio.create_task(daemon_app.serve_forever(), name="Daemon Task")

    try:
        yield {"rc": rc, "db": db}
    finally:
        await daemon_app.stop()
        await daemon_app.wait_stopped()

        try:
            daemon_task.cancel()
            await daemon_task
        except asyncio.CancelledError:
            pass

        await rc.aclose()
        await db.close()

        from app.redis.pool import connection_pool
        connection_pool.close()
        logger.info("End of app lifespan")
