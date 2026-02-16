from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    TaskID,
    TimeElapsedColumn
)

from app.database import PostgresqlDB, db_lifespan
from app.database.seeding import SeedTarget, SeederOrchestrator, SeederTarget, SEEDER_TO_CLI
from app.logging import get_logger


@db_lifespan
async def cmd_seed(db: PostgresqlDB, target: SeedTarget):
    logger = get_logger(__name__)
    orchestrator = SeederOrchestrator(db, target)
    execution_order_string = " -> ".join(f"({", ".join(SEEDER_TO_CLI[seeder] for seeder in layer)})" for layer in orchestrator.execution_order)
    logger.info(f"Seed execution order: {execution_order_string}")

    progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        TextColumn("[white]({task.completed}/{task.total})"),
        BarColumn(pulse_style="dim"),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeRemainingColumn(compact=True),
        TimeElapsedColumn()
    )

    seeder_tasks: dict[SeederTarget, TaskID] = {}

    for target, seeder in orchestrator.seeders.items():
        seeder_tasks[target] = progress.add_task(target.seed_title, start=False, total=seeder.total)

    overall_task = progress.add_task("Total", total=orchestrator.total)
    overall_progress = 0

    progress_table = Table.grid()
    panel = Panel.fit(
        progress,
        title="Seeding the Database",
        border_style="green",
        padding=(1, 3)
    )
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
