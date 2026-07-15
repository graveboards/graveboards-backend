"""CLI command for fixture status and validation.

Usage:
    manage fixtures status [--instance] [--promoted] [--detailed] [--gaps]

Examples:
    manage fixtures status
    manage fixtures status --instance
    manage fixtures status --promoted --detailed
    manage fixtures status --instance --promoted --gaps

Flags:
    --instance    Show only instance/ fixtures status
    --promoted    Show only tests/fixtures/ promoted status  
    --detailed    Include detailed file lists
    --gaps        Show missing fixture gaps
"""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Optional
from datetime import datetime
from rich.console import Console
from rich.columns import Columns
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich import box

from app.fixtures.paths import TEST_FIXTURES_DIR, QUEUE_TEST_FIXTURES_DIR, REQUEST_TEST_FIXTURES_DIR, FIXTURES_DIR
from app.fixtures.metadata_io import load_metadata, save_metadata
from app.fixtures.constants import RULESETS, SCORE_TYPES
from app.fixtures.health import check_category_health

console = Console()


def count_files(path):
    """Count JSON files in a path."""
    return len(list(path.glob("*.json"))) if path.exists() else 0


def get_instance_counts():
    """Get fixture counts for instance/ directory."""
    counts = {}
    for category in ["beatmaps", "beatmapsets", "beatmap_scores", "beatmap_attributes"]:
        path = FIXTURES_DIR / category
        counts[category] = count_files(path)

    users_path = FIXTURES_DIR / "users"
    if users_path.exists():
        counts["users"] = {r: count_files(users_path / r) for r in RULESETS}
    else:
        counts["users"] = {r: 0 for r in RULESETS}

    scores_path = FIXTURES_DIR / "scores"
    if scores_path.exists():
        counts["scores"] = {t: count_files(scores_path / t) for t in SCORE_TYPES}
    else:
        counts["scores"] = {t: 0 for t in SCORE_TYPES}

    for category in ["queues", "requests"]:
        path = FIXTURES_DIR / category
        counts[category] = count_files(path)

    return counts


def get_promoted_counts():
    """Get fixture counts for tests/fixtures/ directory."""
    counts = {}
    for category in ["beatmaps", "beatmapsets", "beatmap_scores", "beatmap_attributes"]:
        path = TEST_FIXTURES_DIR / category
        counts[category] = count_files(path)

    users_path = TEST_FIXTURES_DIR / "users"
    if users_path.exists():
        counts["users"] = {r: count_files(users_path / r) for r in RULESETS}
    else:
        counts["users"] = {r: 0 for r in RULESETS}

    scores_path = TEST_FIXTURES_DIR / "scores"
    if scores_path.exists():
        counts["scores"] = {t: count_files(scores_path / t) for t in SCORE_TYPES}
    else:
        counts["scores"] = {t: 0 for t in SCORE_TYPES}

    counts["queues"] = count_files(QUEUE_TEST_FIXTURES_DIR)
    counts["requests"] = count_files(REQUEST_TEST_FIXTURES_DIR)

    return counts


def format_status_icon(count: int, meta_count: int, is_empty_ok: bool = True) -> str:
    """Format sync status with icon."""
    if count == 0 and is_empty_ok:
        return "[green]✓[/green]"
    return "[green]✓[/green]" if meta_count == count else "[red]✗[/red]"


def format_coverage(count: int, expected: int) -> str:
    """Format coverage percentage with color."""
    if expected == 0:
        return "[green]100%[/green]" if count == 0 else "[yellow]N/A[/yellow]"
    percentage = (count / expected) * 100
    if percentage >= 100:
        return f"[green]{percentage:.0f}%[/green]"
    elif percentage >= 80:
        return f"[yellow]{percentage:.1f}%[/yellow]"
    else:
        return f"[red]{percentage:.1f}%[/red]"


def create_instance_table(instance_counts, metadata):
    """Create table for instance/ fixtures."""
    table = Table(box=box.SQUARE, padding=0)
    table.add_column("Category", style="bold cyan", width=14)
    table.add_column("Meta", style="magenta", width=8)
    table.add_column("Disk", style="yellow", width=8)
    table.add_column("Status", style="", width=8)

    sample_metadata = metadata.get("samples", {})

    for category in ["beatmaps", "beatmapsets", "beatmap_scores", "beatmap_attributes"]:
        disk_count = instance_counts.get(category, 0)
        meta_count = sample_metadata.get(category, {}).get("count", 0)
        status = format_status_icon(disk_count, meta_count, is_empty_ok=False)
        table.add_row(category, str(meta_count), str(disk_count), status)

    users_disk = sum(instance_counts.get("users", {}).values())
    users_meta = sample_metadata.get("users", {}).get("count", 0)
    users_status = format_status_icon(users_disk, users_meta, is_empty_ok=True)
    table.add_row("[b]users[/b]", str(users_meta), str(users_disk), users_status)

    for ruleset in RULESETS:
        rule_disk = instance_counts.get("users", {}).get(ruleset, 0)
        rule_meta = sample_metadata.get("users", {}).get("per_ruleset", {}).get(ruleset, 0)
        rule_status = format_status_icon(rule_disk, rule_meta, is_empty_ok=True)
        table.add_row(f"  {ruleset}", str(rule_meta), str(rule_disk), rule_status)

    scores_disk = sum(instance_counts.get("scores", {}).values())
    scores_meta = sample_metadata.get("scores", {}).get("count", 0)
    scores_status = format_status_icon(scores_disk, scores_meta, is_empty_ok=True)
    table.add_row("[b]scores[/b]", str(scores_meta), str(scores_disk), scores_status)

    for score_type in SCORE_TYPES:
        type_disk = instance_counts.get("scores", {}).get(score_type, 0)
        type_meta = sample_metadata.get("scores", {}).get("per_type", {}).get(score_type, 0)
        type_status = format_status_icon(type_disk, type_meta, is_empty_ok=True)
        table.add_row(f"  {score_type}", str(type_meta), str(type_disk), type_status)

    for category in ["queues", "requests"]:
        disk_count = instance_counts.get(category, 0)
        meta_count = sample_metadata.get(category, {}).get("count", 0)
        status = format_status_icon(disk_count, meta_count, is_empty_ok=True)
        table.add_row(f"[b]{category}[/b]", str(meta_count), str(disk_count), status)

    return table


def create_promoted_table(promoted_counts, metadata):
    """Create table for promoted fixtures."""
    table = Table(box=box.SQUARE, padding=0)
    table.add_column("Category", style="bold cyan", width=14)
    table.add_column("Meta", style="magenta", width=8)
    table.add_column("Disk", style="yellow", width=8)
    table.add_column("Status", style="", width=8)
    table.add_column("Coverage", style="", width=10)

    promoted_metadata = metadata.get("promoted_fixtures", {})

    for category in ["beatmaps", "beatmapsets", "beatmap_scores", "beatmap_attributes"]:
        meta_count = promoted_metadata.get(category, {}).get("count", 0)
        disk_count = promoted_counts.get(category, 0)
        status = format_status_icon(disk_count, meta_count, is_empty_ok=True)
        coverage = format_coverage(disk_count, meta_count)
        table.add_row(category, str(meta_count), str(disk_count), status, coverage)

    users_meta = promoted_metadata.get("users", {}).get("count", 0)
    users_disk = sum(promoted_counts.get("users", {}).values())
    users_status = format_status_icon(users_disk, users_meta, is_empty_ok=True)
    users_coverage = format_coverage(users_disk, users_meta)
    table.add_row("[b]users[/b]", str(users_meta), str(users_disk), users_status, users_coverage)

    for ruleset in RULESETS:
        rule_meta = promoted_metadata.get("users", {}).get("per_ruleset", {}).get(ruleset, 0)
        rule_disk = promoted_counts.get("users", {}).get(ruleset, 0)
        rule_status = format_status_icon(rule_disk, rule_meta, is_empty_ok=True)
        rule_coverage = format_coverage(rule_disk, rule_meta)
        table.add_row(f"  {ruleset}", str(rule_meta), str(rule_disk), rule_status, rule_coverage)

    scores_meta = promoted_metadata.get("scores", {}).get("count", 0)
    scores_disk = sum(promoted_counts.get("scores", {}).values())
    scores_status = format_status_icon(scores_disk, scores_meta, is_empty_ok=True)
    scores_coverage = format_coverage(scores_disk, scores_meta)
    table.add_row("[b]scores[/b]", str(scores_meta), str(scores_disk), scores_status, scores_coverage)

    for score_type in SCORE_TYPES:
        type_meta = promoted_metadata.get("scores", {}).get("per_type", {}).get(score_type, 0)
        type_disk = promoted_counts.get("scores", {}).get(score_type, 0)
        type_status = format_status_icon(type_disk, type_meta, is_empty_ok=True)
        type_coverage = format_coverage(type_disk, type_meta)
        table.add_row(f"  {score_type}", str(type_meta), str(type_disk), type_status, type_coverage)

    for category in ["queues", "requests"]:
        meta_count = promoted_metadata.get(category, {}).get("count", 0)
        disk_count = promoted_counts.get(category, 0)
        status = format_status_icon(disk_count, meta_count, is_empty_ok=True)
        coverage = format_coverage(disk_count, meta_count)
        table.add_row(f"[b]{category}[/b]", str(meta_count), str(disk_count), status, coverage)

    return table


def get_category_gaps():
    """Get detailed gap information for each category."""
    categories = [
        "beatmaps", "beatmapsets", "users", "scores",
        "beatmap_scores", "beatmap_attributes"
    ]
    gaps = []
    
    for category in categories:
        health = check_category_health(category)
        if health.expected_count > 0 and health.actual_count < health.expected_count:
            expected_list = sorted([f.name for f in get_test_fixture_path(category).glob("*.json")])
            
            gaps.append({
                "category": category,
                "expected_count": health.expected_count,
                "actual_count": health.actual_count,
                "missing_count": health.expected_count - health.actual_count,
                "coverage_percentage": health.coverage_percentage,
                "expected_files": expected_list
            })
    
    return gaps


def show_gaps(promoted_counts):
    """Show missing fixture gaps."""
    from app.fixtures.paths import get_test_fixture_path
    
    gaps = get_category_gaps()
    
    if not gaps:
        console.print("[green]✅ All promoted fixtures are complete![/green]")
        return
    
    table = Table(title="[bold yellow]Missing Fixtures[/bold yellow]", box=box.SIMPLE_HEAD)
    table.add_column("Category", style="cyan")
    table.add_column("Missing", style="red")
    table.add_column("Coverage", style="white")
    table.add_column("Files", style="white")
    
    for gap in gaps:
        table.add_row(
            gap["category"],
            str(gap["missing_count"]),
            format_coverage(gap["actual_count"], gap["expected_count"]),
            f"{gap['actual_count']}/{gap['expected_count']}"
        )
    
    console.print(table)


def format_percentage(value: float) -> str:
    """Format a percentage with color coding."""
    if value >= 100:
        return f"[green]{value:.1f}%[/green]"
    elif value >= 80:
        return f"[yellow]{value:.1f}%[/yellow]"
    else:
        return f"[red]{value:.1f}%[/red]"


async def cmd_fixture_status(
    instance: bool = False,
    promoted: bool = False,
    detailed: bool = False,
    gaps: bool = False
) -> None:
    """Show fixture status for instance and promoted fixtures.
    
    Args:
        instance: Show only instance/ fixtures
        promoted: Show only tests/fixtures/ promoted fixtures
        detailed: Include detailed file lists
        gaps: Show missing fixture gaps (only for promoted)
    """
    from app.fixtures.reader import FixtureReader
    from app.fixtures.paths import FIXTURES_DIR, get_fixture_path

    metadata = load_metadata()

    manager = FixtureReader()
    for cat in ["beatmaps", "beatmapsets", "beatmap_scores", "beatmap_attributes", "users", "scores"]:
        await manager.refresh_category_metadata(cat)

    samples = metadata.get("samples", {})
    for category in ["beatmaps", "beatmapsets", "beatmap_scores", "beatmap_attributes"]:
        cat_path = FIXTURES_DIR / category
        disk_count = len(list(cat_path.glob("*.json"))) if cat_path.exists() else 0
        samples.setdefault(category, {})["count"] = disk_count

    if samples.get("users"):
        users_path = FIXTURES_DIR / "users"
        total = 0
        per_ruleset = samples["users"].get("per_ruleset", {})
        for ruleset in ["osu", "taiko", "fruits", "mania"]:
            rpath = users_path / ruleset
            rc = len(list(rpath.glob("*.json"))) if rpath.exists() else 0
            total += rc
            per_ruleset[ruleset] = rc
        samples["users"]["count"] = total
        samples["users"]["per_ruleset"] = per_ruleset

    if samples.get("scores"):
        scores_path = FIXTURES_DIR / "scores"
        total = 0
        per_type = samples["scores"].get("per_type", {})
        for stype in ["best", "firsts", "recent"]:
            spath = scores_path / stype
            sc = len(list(spath.glob("*.json"))) if spath.exists() else 0
            total += sc
            per_type[stype] = sc
        samples["scores"]["count"] = total
        samples["scores"]["per_type"] = per_type

    metadata["samples"] = samples
    save_metadata(metadata)
    metadata = load_metadata()

    instance_counts = get_instance_counts()
    promoted_counts = get_promoted_counts()
    
    # Determine what to show
    show_instance = not promoted  # Show instance unless --promoted is specified
    show_promoted = not instance  # Show promoted unless --instance is specified
    
    # Header
    header_table = Table(show_header=False, box=None, padding=(0, 1))
    header_table.add_column(justify="center")
    header_table.add_row("")
    header_table.add_row("[bold]=== Fixture Status ===[/bold]")
    header_table.add_row(f"Last updated: {metadata.get('last_updated', 'Never')}")
    header_table.add_row(f"Source: {metadata.get('source', 'N/A')}")
    header_table.add_row("")
    header_panel = Panel(header_table, box=box.ROUNDED, padding=(0, 2), expand=False)
    
    if show_instance and show_promoted:
        # Horizontal layout - both panels side by side
        instance_table = create_instance_table(instance_counts, metadata)
        instance_panel = Panel(
            instance_table, 
            title="[bold cyan]Transient (instance/)[/bold cyan]", 
            box=box.ROUNDED, 
            padding=(0, 0)
        )
        
        promoted_table = create_promoted_table(promoted_counts, metadata)
        promoted_panel = Panel(
            promoted_table, 
            title="[bold cyan]Promoted (tests/)[/bold cyan]", 
            box=box.ROUNDED, 
            padding=(0, 0)
        )
        
        side_by_side = Columns([instance_panel, promoted_panel], equal=True, padding=(0, 1))
        console.print(Group(header_panel, side_by_side))
        
        if detailed:
            console.print("\n[bold]Instance Files:[/bold]")
            for category in ["beatmaps", "beatmapsets", "beatmap_scores", "beatmap_attributes", "queues", "requests"]:
                path = FIXTURES_DIR / category
                if path.exists():
                    files = sorted([f.name for f in path.glob("*.json")])
                    if files:
                        console.print(f"\n  [cyan]{category}[/cyan]")
                        for f in files[:10]:
                            console.print(f"    {f}")
                        if len(files) > 10:
                            console.print(f"    ... and {len(files) - 10} more")
                    else:
                        console.print(f"\n  [red]{category}: (empty)[/red]")
            
            users_path = FIXTURES_DIR / "users"
            if users_path.exists():
                console.print("\n  [cyan]users[/cyan]")
                for ruleset in RULESETS:
                    rule_path = users_path / ruleset
                    if rule_path.exists():
                        files = sorted([f.name for f in rule_path.glob("*.json")])
                        if files:
                            console.print(f"    [yellow]{ruleset}:[/yellow] {len(files)} files")
                        else:
                            console.print(f"    [red]{ruleset}: (empty)[/red]")
            
            console.print("\n[bold]Promoted Files:[/bold]")
            for category in ["beatmaps", "beatmapsets", "beatmap_scores", "beatmap_attributes", "queues", "requests"]:
                path = TEST_FIXTURES_DIR / category
                if path.exists():
                    files = sorted([f.name for f in path.glob("*.json")])
                    if files:
                        console.print(f"\n  [cyan]{category}[/cyan]")
                        for f in files[:10]:
                            console.print(f"    {f}")
                        if len(files) > 10:
                            console.print(f"    ... and {len(files) - 10} more")
                    else:
                        console.print(f"\n  [red]{category}: (empty)[/red]")
            
            users_path = TEST_FIXTURES_DIR / "users"
            if users_path.exists():
                console.print("\n  [cyan]users[/cyan]")
                for ruleset in RULESETS:
                    rule_path = users_path / ruleset
                    if rule_path.exists():
                        files = sorted([f.name for f in rule_path.glob("*.json")])
                        if files:
                            console.print(f"    [yellow]{ruleset}:[/yellow] {len(files)} files")
                        else:
                            console.print(f"    [red]{ruleset}: (empty)[/red]")
        
        if gaps:
            show_gaps(promoted_counts)
    
    else:
        # Vertical layout - one at a time
        if show_instance:
            instance_table = create_instance_table(instance_counts, metadata)
            instance_panel = Panel(
                instance_table, 
                title="[bold cyan]Transient (instance/)[/bold cyan]", 
                box=box.ROUNDED, 
                padding=(0, 0)
            )
            console.print(instance_panel)
            
            if detailed:
                console.print("\n[bold]Instance Files:[/bold]")
                for category in ["beatmaps", "beatmapsets", "beatmap_scores", "beatmap_attributes", "queues", "requests"]:
                    path = FIXTURES_DIR / category
                    if path.exists():
                        files = sorted([f.name for f in path.glob("*.json")])
                        if files:
                            console.print(f"\n  [cyan]{category}[/cyan]")
                            for f in files[:10]:
                                console.print(f"    {f}")
                            if len(files) > 10:
                                console.print(f"    ... and {len(files) - 10} more")
                        else:
                            console.print(f"\n  [red]{category}: (empty)[/red]")
                
                users_path = FIXTURES_DIR / "users"
                if users_path.exists():
                    console.print("\n  [cyan]users[/cyan]")
                    for ruleset in RULESETS:
                        rule_path = users_path / ruleset
                        if rule_path.exists():
                            files = sorted([f.name for f in rule_path.glob("*.json")])
                            if files:
                                console.print(f"    [yellow]{ruleset}:[/yellow] {len(files)} files")
                            else:
                                console.print(f"    [red]{ruleset}: (empty)[/red]")
        
        if show_promoted:
            console.print("\n") if show_instance else None
            promoted_table = create_promoted_table(promoted_counts, metadata)
            promoted_panel = Panel(
                promoted_table, 
                title="[bold cyan]Promoted (tests/)[/bold cyan]", 
                box=box.ROUNDED, 
                padding=(0, 0)
            )
            console.print(promoted_panel)
            
            if detailed:
                console.print("\n[bold]Promoted Files:[/bold]")
                for category in ["beatmaps", "beatmapsets", "beatmap_scores", "beatmap_attributes", "queues", "requests"]:
                    path = TEST_FIXTURES_DIR / category
                    if path.exists():
                        files = sorted([f.name for f in path.glob("*.json")])
                        if files:
                            console.print(f"\n  [cyan]{category}[/cyan]")
                            for f in files[:10]:
                                console.print(f"    {f}")
                            if len(files) > 10:
                                console.print(f"    ... and {len(files) - 10} more")
                        else:
                            console.print(f"\n  [red]{category}: (empty)[/red]")
                
                users_path = TEST_FIXTURES_DIR / "users"
                if users_path.exists():
                    console.print("\n  [cyan]users[/cyan]")
                    for ruleset in RULESETS:
                        rule_path = users_path / ruleset
                        if rule_path.exists():
                            files = sorted([f.name for f in rule_path.glob("*.json")])
                            if files:
                                console.print(f"    [yellow]{ruleset}:[/yellow] {len(files)} files")
                            else:
                                console.print(f"    [red]{ruleset}: (empty)[/red]")
        
        if gaps and show_promoted:
            show_gaps(promoted_counts)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Show fixture status for instance and promoted fixtures"
    )
    parser.add_argument(
        "--instance", "-i",
        action="store_true",
        help="Show only instance/ fixtures"
    )
    parser.add_argument(
        "--promoted", "-p",
        action="store_true",
        help="Show only tests/fixtures/ promoted fixtures"
    )
    parser.add_argument(
        "--detailed", "-d",
        action="store_true",
        help="Include detailed file lists"
    )
    parser.add_argument(
        "--gaps", "-g",
        action="store_true",
        help="Show missing fixture gaps (only for promoted)"
    )
    
    args = parser.parse_args()
    asyncio.run(cmd_fixture_status(
        instance=args.instance,
        promoted=args.promoted,
        detailed=args.detailed,
        gaps=args.gaps
    ))


if __name__ == "__main__":
    main()
