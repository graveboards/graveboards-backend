import sys

from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    TaskID,
    TimeElapsedColumn,
)

from app.database import PostgresqlDB, db_lifespan
from app.database.seeding import (
    CLI_TO_SEEDER,
    SeedTarget,
    SeederOrchestrator,
    SeederTarget,
    SEEDER_TO_CLI,
)
from app.database.seeding.profiles import get_profile
from app.database.seeding.fixture_loader import load_seeding_data
from app.fixtures.queue_request_generator import QueueRequestFixtureGenerator
from app.logging import get_logger


@db_lifespan
async def cmd_seed(
    db: PostgresqlDB,
    target: SeedTarget,
    ensure_fixtures: bool = False,
    profile_name: str = "default",
):
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
        if ensure_fixtures:
            profile = get_profile(profile_name)
            queue_count = profile.queue_count
            request_count = profile.request_count
        else:
            # Check if queues/requests exist, generate if not
            from app.database.seeding.fixture_loader import check_fixtures

            fixture_status = check_fixtures(internal_targets)
            if fixture_status["counts"].get("queues", 0) == 0:
                queue_count = 10
                request_count = 100
            else:
                # Skip generation if queues already exist
                needs_generation = False

        if needs_generation:
            logger.info(
                f"Generating queue and request fixtures ({queue_count} queues, {request_count} requests)..."
            )

            # Clean up existing queue/request fixtures to avoid stale/corrupted data
            from pathlib import Path

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
            if seed_target == SeederTarget.BEATMAP and "beatmap_tags" in seeding_data:
                seeder.set_beatmap_tags(seeding_data["beatmap_tags"])

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

    for target, seeder in orchestrator.seeders.items():
        seeder_tasks[target] = progress.add_task(target.seed_title, start=False, total=seeder.total)

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
