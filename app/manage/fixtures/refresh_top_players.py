from typing import Optional

from rich.console import Console
from rich.table import Table

from app.fixtures.utils import RULESETS
from app.fixtures.fetcher import FixtureDataFetcher
from app.redis import RedisClient
from app.logging import get_logger

console = Console()
logger = get_logger(__name__)


async def cmd_refresh_top_players(
    rulesets: Optional[list[str]] = None,
    count: int = 1000,
) -> None:
    rc = RedisClient()
    try:
        fetcher = FixtureDataFetcher(rc)
        fetcher.logger = logger

        if rulesets is None:
            rulesets = RULESETS

        console.print("\n[bold blue]Refreshing top players from osu! API...[/bold blue]")
        console.print(f"[bold]Rulesets:[/bold] {', '.join(rulesets)}")
        console.print(f"[bold]Count per ruleset:[/bold] {count}\n")

        fetched = await fetcher.fetch_top_players(rulesets=rulesets, count_per_ruleset=count)

        console.print("\n[bold green]Top players refresh complete![/bold green]\n")
        console.print("[bold]Fetched:[/bold]")
        table = Table(show_header=False)
        table.add_column("Ruleset")
        table.add_column("Count")
        for ruleset, player_ids in fetched.items():
            table.add_row(ruleset, str(len(player_ids)))
        console.print(table)
        console.print()
    finally:
        await rc.aclose()
