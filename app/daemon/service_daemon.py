import asyncio

from app.redis import RedisClient
from app.database import PostgresqlDB
from app.logging import get_logger
from .services import ServiceClass, ServiceType

logger = get_logger(__name__)


class ServiceDaemon:
    def __init__(self, rc: RedisClient, db: PostgresqlDB):
        self.rc = rc
        self.db = db

        self.services: dict[ServiceClass, ServiceType] = {}
        self.service_tasks: dict[ServiceClass, asyncio.Task] = {}

    async def run(self):
        logger.info(f"Starting up daemon: loading registered services ({len(self.services)})")

        for service_class, service in self.services.items():
            class_name = service.__class__.__name__
            self.service_tasks[service_class] = asyncio.create_task(service.run(), name=f"{class_name} Service")
            logger.info(f"Started service: {class_name}")

        try:
            await asyncio.gather(*self.service_tasks.values())
        except Exception as e:
            logger.exception("Daemon encountered an error:\n%s", e)
            raise

    def register_service(self, service_class: ServiceClass):
        self.services[service_class] = service_class.value(self.rc, self.db)

    async def shutdown(self):
        logger.info(f"Shutting down daemon: terminating service tasks ({len(self.service_tasks)})")

        for task in self.service_tasks.values():
            task.cancel()

        for task in self.service_tasks.values():
            try:
                await task
            except asyncio.CancelledError:
                pass
