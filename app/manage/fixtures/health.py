"""CLI command for fixture health checks.

Usage:
    manage fixtures health [--category CATEGORY] [--detailed] [--format FORMAT]

Examples:
    manage fixtures health
    manage fixtures health --category beatmaps
    manage fixtures health --detailed
    manage fixtures health --format json
"""

import argparse
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.box import SIMPLE_HEAD

from app.fixtures.health import check_all_categories, get_incomplete_categories, check_category_health
from app.fixtures.utils import RULESETS, SCORE_TYPES


console = Console()


def format_percentage(value: float) -> str:
    """Format a percentage with color coding."""
    if value >= 100:
        return f"[green]{value:.1f}%[/green]"
    elif value >= 80:
        return f"[yellow]{value:.1f}%[/yellow]"
    else:
        return f"[red]{value:.1f}%[/red]"


async def cmd_fixture_health(
    category: str | None = None,
    detailed: bool = False,
    format_type: str = "text"
) -> None:
    """Check fixture data health and completeness.
    
    Args:
        category: Specific category to check (None for all)
        detailed: Show detailed file lists
        format_type: Output format (text or json)
    """
    if category:
        health = check_category_health(category)
        
        if format_type == "json":
            result = {
                "category": health.category,
                "expected_count": health.expected_count,
                "actual_count": health.actual_count,
                "coverage_percentage": health.coverage_percentage,
                "complete": health.complete,
                "integrity_errors": health.integrity_errors,
                "file_count": len(health.files)
            }
            console.print(json.dumps(result, indent=2))
        else:
            table = Table(
                title=f"[bold]Fixture Health: {health.category}[/bold]",
                box=SIMPLE_HEAD
            )
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("Category", health.category)
            table.add_row("Expected Count", str(health.expected_count))
            table.add_row("Actual Count", str(health.actual_count))
            table.add_row("Coverage", format_percentage(health.coverage_percentage))
            
            status_icon = "✅" if health.complete else "❌"
            table.add_row("Status", f"{status_icon} {'Complete' if health.complete else 'Incomplete'}")
            
            if health.integrity_errors:
                table.add_row("Integrity Errors", f"[red]{len(health.integrity_errors)} error(s)[/red]")
            else:
                table.add_row("Integrity", "[green]✓ OK[/green]")
            
            console.print(table)
            
            if detailed and health.files:
                console.print(f"\n[bold]Files ({len(health.files)}):[/bold]")
                for filename in sorted(health.files):
                    console.print(f"  {filename}")
            
            if health.integrity_errors and detailed:
                console.print("\n[bold red]Integrity Errors:[/bold red]")
                for error in health.integrity_errors:
                    console.print(f"  • {error}")
    else:
        report = check_all_categories()
        
        if format_type == "json":
            result = {
                "generated_at": report.generated_at.isoformat(),
                "total_categories": report.total_categories,
                "complete_categories": report.complete_categories,
                "incomplete_categories": report.incomplete_categories,
                "overall_coverage_percentage": report.coverage_percentage,
                "categories": [
                    {
                        "category": c.category,
                        "expected_count": c.expected_count,
                        "actual_count": c.actual_count,
                        "coverage_percentage": c.coverage_percentage,
                        "complete": c.complete
                    }
                    for c in report.categories
                ],
                "missing_gaps": report.missing_gaps
            }
            console.print(json.dumps(result, indent=2))
        else:
            header = Text("Fixture Health Check", style="bold magenta")
            header.append("\n", style="")
            header.append(f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}", style="dim")
            console.print(Panel(header, box=SIMPLE_HEAD))
            
            stats_table = Table(show_header=False)
            stats_table.add_column("Stat", style="cyan")
            stats_table.add_column("Value", style="white")
            
            stats_table.add_row("Total Categories", str(report.total_categories))
            stats_table.add_row("Complete", f"[green]{report.complete_categories}[/green]")
            stats_table.add_row("Incomplete", f"[red]{report.incomplete_categories}[/red]")
            stats_table.add_row("Overall Coverage", format_percentage(report.coverage_percentage))
            
            console.print(stats_table)
            
            if report.incomplete_categories > 0:
                console.print("\n[bold yellow]Incomplete Categories:[/bold yellow]")
                for gap in report.missing_gaps:
                    console.print(
                        f"  • {gap['category']}: {gap['coverage_percentage']:.1f}% "
                        f"({gap['missing_count']} missing)"
                    )
            
            if detailed:
                console.print("\n[bold]Category Details:[/bold]")
                detail_table = Table(box=SIMPLE_HEAD)
                detail_table.add_column("Category", style="cyan")
                detail_table.add_column("Expected", style="white")
                detail_table.add_column("Actual", style="white")
                detail_table.add_column("Coverage", style="white")
                detail_table.add_column("Status", style="white")
                
                for cat in report.categories:
                    status = "✅" if cat.complete else "❌"
                    detail_table.add_row(
                        cat.category,
                        str(cat.expected_count),
                        str(cat.actual_count),
                        format_percentage(cat.coverage_percentage),
                        f"{status} {'Complete' if cat.complete else 'Incomplete'}"
                    )
                
                console.print(detail_table)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Check fixture data health and completeness"
    )
    parser.add_argument(
        "--category", "-c",
        choices=["beatmaps", "beatmapsets", "users", "scores", "beatmap_scores", "beatmap_attributes"],
        help="Specific category to check"
    )
    parser.add_argument(
        "--detailed", "-d",
        action="store_true",
        help="Show detailed file lists"
    )
    parser.add_argument(
        "--format", "-f",
        dest="format_type",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    
    args = parser.parse_args()
    cmd_fixture_health(
        category=args.category,
        detailed=args.detailed,
        format_type=args.format_type
    )


if __name__ == "__main__":
    main()
