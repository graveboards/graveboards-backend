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
"""Mapping of ``SeederTarget`` to concrete ``Seeder`` implementation.

This registry allows the orchestrator to dynamically instantiate the correct seeder 
class for each logical domain target.
"""


class SeederOrchestrator:
    """Coordinates dependency-aware, layered database seeding.

    The orchestrator:
        - Normalizes CLI targets into internal ``SeederTarget`` values
        - Resolves transitive dependencies via topological layering
        - Executes seeders layer-by-layer
        - Runs independent seeders within a layer concurrently
        - Streams progress events as an async iterator

    Seeding is deterministic with respect to dependency order while still leveraging
    asyncio concurrency for independent targets.
    """
    def __init__(self, db: PostgresqlDB, *targets: SeedTarget):
        """Initialize the orchestrator for the given seed targets.

        Args:
            db:
                Database interface.
            *targets:
                CLI-facing seed targets to execute.

        Raises:
            TypeError:
                If invalid ``SeedTarget`` values are provided.
        """
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
        """Execute all seeders in dependency order.

        Seeders are executed in topological layers. Within each layer, seeders run
        concurrently. Progress events are streamed as they are produced.

        Yields:
            SeedEvent: Incremental progress updates for each target.

        Raises:
            Exception:
                Propagates seeder-level exceptions.
        """
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
        """Translate CLI targets into internal ``SeederTarget`` values.

        If ALL is specified, all ``SeederTarget`` members are returned.

        Args:
            targets:
                User-specified CLI targets.

        Returns:
            A normalized set of ``SeederTarget`` values.
        """
        if SeedTarget.ALL in targets:
            return {member for member in SeederTarget}

        return {CLI_TO_SEEDER[t] for t in targets}
