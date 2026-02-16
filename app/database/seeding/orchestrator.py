import asyncio
from typing import AsyncIterator

from app.database import PostgresqlDB
from .seeders import Seeder, UserSeeder, BeatmapSeeder, QueueSeeder, RequestSeeder
from .target import SeedTarget, SeederTarget, CLI_TO_SEEDER
from .dependencies import resolve_dependencies
from .event import SeedEvent

SEEDERS: dict[SeederTarget, type[Seeder]] = {
    SeederTarget.USER: UserSeeder,
    SeederTarget.BEATMAP: BeatmapSeeder,
    SeederTarget.QUEUE: QueueSeeder,
    SeederTarget.REQUEST: RequestSeeder
}


class SeederOrchestrator:
    def __init__(self, db: PostgresqlDB, *targets: SeedTarget):
        self.db = db
        targets = set(targets)

        if not targets.issubset(set(SeedTarget)):
            raise TypeError(f"Invalid target(s) provided, all must be {SeedTarget}")

        self.targets: set[SeederTarget] = self._normalize_cli_targets(targets)
        self.execution_order: list[list[SeederTarget]] = resolve_dependencies(self.targets)
        self.seeders = {
            target: SEEDERS[target](db)
            for layer in self.execution_order
            for target in layer
        }
        self.totals = {
            target: seeder.total
            for target, seeder in self.seeders.items()
        }
        self.total = sum(t for t in self.totals.values())

    async def run_seeders(self) -> AsyncIterator[SeedEvent]:
        queue: asyncio.Queue[SeedEvent | None] = asyncio.Queue()

        for layer in self.execution_order:
            async def wrap(target: SeederTarget):
                try:
                    await self.seeders[target].seed(queue=queue)
                finally:
                    await queue.put(None)

            tasks = [
                asyncio.create_task(
                    wrap(target),
                    name=f"{target.seed_title} Seed Task"
                )
                for target in layer
            ]

            remaining = len(layer)

            while remaining:
                event = await queue.get()

                if event is None:
                    remaining -= 1
                    continue

                yield event

            await asyncio.gather(*tasks)

    @staticmethod
    def _normalize_cli_targets(targets: set[SeedTarget]) -> set[SeederTarget]:
        if SeedTarget.ALL in targets:
            return {member for member in SeederTarget}

        return {CLI_TO_SEEDER[t] for t in targets}
