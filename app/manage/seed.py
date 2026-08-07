from __future__ import annotations

import sys
from typing import Any, cast

from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from app.config import PROJECT_ROOT
from app.database import PostgresqlDB, db_lifespan
from app.database.seeding import (
    CLI_TO_SEEDER,
    SEEDER_TO_CLI,
    SeederOrchestrator,
    SeederTarget,
    SeedTarget,
)
from app.database.seeding.fixture_loader import load_seeding_data
from app.database.seeding.profiles import get_profile
from app.fixtures.queue_request_generator import QueueRequestFixtureGenerator
from app.observability.logging import get_logger

DEFAULT_QUEUE_COUNT = 10
DEFAULT_REQUEST_COUNT = 100


@db_lifespan
async def cmd_seed(
    db: PostgresqlDB,
    target: SeedTarget,
    ensure_fixtures: bool = False,
    profile_name: str = "default",
) -> None:
    """Seed the database with fixtures.

    Args:
        db: Database connection
        target: What to seed (ALL, USERS, BEATMAPS, QUEUES, REQUESTS)
        ensure_fixtures: If True, auto-fetch/generate missing fixtures before seeding
        profile_name: Profile name for fixture counts (default, minimal, comprehensive)
    """
    logger = get_logger(__name__)

    # Resolve internal seed targets
    if target == SeedTarget.ALL:
        internal_targets = {
            SeederTarget.USER,
            SeederTarget.BEATMAP,
            SeederTarget.QUEUE,
            SeederTarget.REQUEST,
        }
    else:
        internal_targets = {CLI_TO_SEEDER[target]}

    # Auto-fetch/generate missing fixtures if requested
    if ensure_fixtures:
        profile = get_profile(profile_name)
        logger.info(f"Using profile: {profile}")

        from app.manage.seed_helpers import ensure_fixtures_async

        if not await ensure_fixtures_async(logger, profile):
            logger.error("Failed to ensure required fixtures. Aborting.")
            sys.exit(1)

    # Generate queues/requests if needed
    needs_generation = (
        SeederTarget.QUEUE in internal_targets or SeederTarget.REQUEST in internal_targets
    )
    if needs_generation:
        queue_count = 0
        request_count = 0

        if ensure_fixtures:
            profile = get_profile(profile_name)
            queue_count = profile.queue_count
            request_count = profile.request_count
        else:
            # Check if queues/requests exist, generate if not
            from app.database.seeding.fixture_loader import check_fixtures

            fixture_status = check_fixtures(internal_targets)
            counts = fixture_status["counts"]
            if isinstance(counts, dict) and counts.get("queues", 0) == 0:
                queue_count = DEFAULT_QUEUE_COUNT
                request_count = DEFAULT_REQUEST_COUNT
            else:
                # Skip generation if queues already exist
                needs_generation = False

        if needs_generation:
            logger.info(
                f"Generating queue and request fixtures ({queue_count} queues, {request_count} requests)..."
            )

            # Clean up existing queue/request fixtures to avoid stale/corrupted data

            queues_path = PROJECT_ROOT / "instance" / "fixtures" / "queues"
            requests_path = PROJECT_ROOT / "instance" / "fixtures" / "requests"
            if queues_path.exists():
                for f in queues_path.glob("queue_*.json"):
                    f.unlink()
            if requests_path.exists():
                for f in requests_path.glob("request_*.json"):
                    f.unlink()

            generator = QueueRequestFixtureGenerator()
            queues = generator.generate_queues(count=queue_count)
            requests = generator.generate_requests(queues=queues, count=request_count)
            generator.save_queues(queues)
            generator.save_requests(requests)
            logger.info(f"Generated {len(queues)} queues and {len(requests)} requests")

    # Load and adapt fixture data
    seeding_data = load_seeding_data(internal_targets)

    # Check if we have data to seed
    total_items = sum(len(data) for data in seeding_data.values())
    if total_items == 0 and not needs_generation:
        logger.warning("No fixture data found in instance/fixtures/. Nothing to seed.")
        logger.info(
            "Run with --ensure-fixtures to auto-fetch/generate data, or populate instance/fixtures/ manually."
        )
        return

    orchestrator = SeederOrchestrator(db, target)
    execution_order_string = " -> ".join(
        f"({', '.join(SEEDER_TO_CLI[seeder] for seeder in layer)})"
        for layer in orchestrator.execution_order
    )
    logger.info(f"Seed execution order: {execution_order_string}")

    # Inject loaded data into seeders
    for seed_target, seeder in orchestrator.seeders.items():
        if seed_target in seeding_data:
            seeder.set_data(seeding_data[seed_target])
            # BeatmapSeeder needs beatmap tags separately
            if seed_target == SeederTarget.BEATMAP:
                beatmap_tags: list[dict[str, Any]] = cast(dict[str, Any], seeding_data).get(
                    "beatmap_tags", []
                )
                if beatmap_tags is not None:
                    from app.database.seeding.seeders.beatmap import BeatmapSeeder

                    if isinstance(seeder, BeatmapSeeder):
                        seeder.set_beatmap_tags(beatmap_tags)

    # Recalculate totals after data is set
    orchestrator._refresh_totals()

    progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        TextColumn("[white]({task.completed}/{task.total})"),
        BarColumn(pulse_style="dim"),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeRemainingColumn(compact=True),
        TimeElapsedColumn(),
    )

    seeder_tasks: dict[SeederTarget, TaskID] = {}

    for _target in orchestrator.seeders:
        seeder = orchestrator.seeders[_target]
        seeder_tasks[_target] = progress.add_task(
            _target.seed_title, start=False, total=seeder.total
        )
    overall_task = progress.add_task("Total", total=orchestrator.total)
    overall_progress = 0

    progress_table = Table.grid()
    panel = Panel.fit(progress, title="Seeding the Database", border_style="green", padding=(1, 3))
    progress_table.add_row(panel)

    with Live(progress_table, refresh_per_second=20):
        async for event in orchestrator.run_seeders():
            task = seeder_tasks[event.target]

            if event.current == 0:
                progress.start_task(task)
                continue

            overall_progress += 1
            progress.update(task, completed=event.current)
            progress.update(overall_task, completed=overall_progress)

        panel.title = "Seeding Completed"
        panel.border_style = "dim green"

    # Realign owned sequences with max(id). Seeders no longer insert explicit
    # primary keys, but this is a cheap safety net for any rows already present.
    await db.reset_sequences()
