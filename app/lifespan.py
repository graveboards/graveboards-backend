import asyncio
from contextlib import asynccontextmanager

from connexion.middleware import ConnexionMiddleware

from .redis import RedisClient
from .database import PostgresqlDB
from .config import CONFIG, get_security_enabled
from .logging import get_logger
from .daemon import Daemon
from .bootstrap import SetupRunner


@asynccontextmanager
async def lifespan(app: ConnexionMiddleware):
    # setup_logging() runs earlier, in the app factory (create_connexion_app),
    # so logging is configured before uvicorn emits its first startup lines.
    logger = get_logger(__name__)
    logger.info("Start of app lifespan")

    from app.observability.metrics.build import set_build_info
    version, commit = set_build_info()
    logger.info(f"Build info: version={version} commit={commit}")

    runner = SetupRunner(CONFIG.bootstrap)

    from app.database.migrations import run_migrations
    run_migrations()

    await runner.run()

    if not get_security_enabled():
        logger.warning("Security has been disabled!")

    rc = RedisClient()
    db = PostgresqlDB()

    cleanup_runner = SetupRunner(CONFIG.bootstrap, rc=rc)
    await cleanup_runner.cleanup_stale_tasks()

    daemon_app = Daemon(rc, db)
    await daemon_app.start()
    daemon_task = asyncio.create_task(daemon_app.serve_forever(), name="Daemon Task")

    try:
        yield {"rc": rc, "db": db, "daemon": daemon_app}
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
