"""CLI command for fixture coverage reports.

Usage:
    manage fixtures report [--category CATEGORY] [--detailed] [--format FORMAT]

Examples:
    manage fixtures report
    manage fixtures report --category beatmaps --detailed
    manage fixtures report --format json
"""

import argparse
import json
from datetime import datetime, timezone
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.box import SIMPLE_HEAD

from app.fixtures.health import check_all_categories, check_category_health
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


async def cmd_fixture_report(
    category: str | None = None,
    detailed: bool = False,
    format_type: str = "text"
) -> None:
    """Generate fixture coverage report.
    
    Args:
        category: Specific category to report on (None for all)
        detailed: Include file lists and detailed breakdown
        format_type: Output format (text or json)
    """
    if category:
        health = check_category_health(category)
        
        if format_type == "json":
            result = {
                "generated_at": (health.last_updated or datetime.now(timezone.utc)).isoformat() if health.last_updated else datetime.now(timezone.utc).isoformat(),
                "category": health.category,
                "expected_count": health.expected_count,
                "actual_count": health.actual_count,
                "coverage_percentage": health.coverage_percentage,
                "complete": health.complete,
                "integrity_valid": len(health.integrity_errors) == 0,
                "files": health.files,
                "integrity_errors": health.integrity_errors
            }
            console.print(json.dumps(result, indent=2))
        else:
            title = Text(f"Coverage Report: {health.category}", style="bold magenta")
            title.append("\n", style="")
            title.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}", style="dim")
            console.print(Panel(title, box=SIMPLE_HEAD))
            
            table = Table(show_header=True, box=SIMPLE_HEAD)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white")
            
            table.add_row("Category", health.category)
            table.add_row("Expected Count", str(health.expected_count))
            table.add_row("Actual Count", str(health.actual_count))
            table.add_row("Coverage", format_percentage(health.coverage_percentage))
            
            status = "✅ Complete" if health.complete else "❌ Incomplete"
            table.add_row("Status", status)
            
            integrity_ok = len(health.integrity_errors) == 0
            table.add_row("Integrity", f"{'✅ OK' if integrity_ok else '❌ Errors'}")
            
            console.print(table)
            
            if detailed:
                if health.files:
                    console.print(f"\n[bold]Files ({len(health.files)}):[/bold]")
                    for filename in sorted(health.files):
                        console.print(f"  {filename}")
                
                if health.integrity_errors:
                    console.print("\n[bold red]Integrity Errors:[/bold red]")
                    for error in health.integrity_errors:
                        console.print(f"  • {error}")
    else:
        report = check_all_categories()
        
        if format_type == "json":
            result = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "summary": {
                    "total_categories": report.total_categories,
                    "complete_categories": report.complete_categories,
                    "incomplete_categories": report.incomplete_categories,
                    "overall_coverage_percentage": report.coverage_percentage
                },
                "categories": [
                    {
                        "category": c.category,
                        "expected_count": c.expected_count,
                        "actual_count": c.actual_count,
                        "coverage_percentage": c.coverage_percentage,
                        "complete": c.complete,
                        "file_count": len(c.files)
                    }
                    for c in report.categories
                ],
                "missing_gaps": report.missing_gaps
            }
            console.print(json.dumps(result, indent=2))
        else:
            title = Text("Fixture Coverage Report", style="bold magenta")
            title.append("\n", style="")
            title.append(f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}", style="dim")
            console.print(Panel(title, box=SIMPLE_HEAD))
            
            summary_table = Table(show_header=False)
            summary_table.add_column("Metric", style="cyan")
            summary_table.add_column("Value", style="white")
            
            summary_table.add_row("Total Categories", str(report.total_categories))
            summary_table.add_row("Complete", f"[green]{report.complete_categories}[/green]")
            summary_table.add_row("Incomplete", f"[red]{report.incomplete_categories}[/red]")
            summary_table.add_row("Overall Coverage", format_percentage(report.coverage_percentage))
            
            console.print(summary_table)
            
            console.print("\n[bold]Category Coverage:[/bold]")
            coverage_table = Table(box=SIMPLE_HEAD)
            coverage_table.add_column("Category", style="cyan")
            coverage_table.add_column("Expected", style="white")
            coverage_table.add_column("Actual", style="white")
            coverage_table.add_column("Coverage", style="white")
            coverage_table.add_column("Status", style="white")
            
            for cat in report.categories:
                status = "✅" if cat.complete else "❌"
                coverage_table.add_row(
                    cat.category,
                    str(cat.expected_count),
                    str(cat.actual_count),
                    format_percentage(cat.coverage_percentage),
                    f"{status} {'Complete' if cat.complete else 'Incomplete'}"
                )
            
            console.print(coverage_table)
            
            if report.missing_gaps:
                console.print("\n[bold yellow]Missing Coverage:[/bold yellow]")
                for gap in report.missing_gaps:
                    console.print(
                        f"  • {gap['category']}: {gap['missing_count']} fixtures missing "
                        f"({gap['coverage_percentage']:.1f}% coverage)"
                    )
            
            if detailed:
                console.print("\n[bold]Detailed File Lists:[/bold]")
                for cat in report.categories:
                    console.print(f"\n[bold]{cat.category}[/bold]")
                    for filename in sorted(cat.files):
                        console.print(f"  {filename}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate fixture coverage report"
    )
    parser.add_argument(
        "--category", "-c",
        choices=["beatmaps", "beatmapsets", "users", "scores", "beatmap_scores", "beatmap_attributes"],
        help="Specific category to report on"
    )
    parser.add_argument(
        "--detailed", "-d",
        action="store_true",
        help="Include detailed file lists"
    )
    parser.add_argument(
        "--format", "-f",
        dest="format_type",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    
    args = parser.parse_args()
    cmd_fixture_report(
        category=args.category,
        detailed=args.detailed,
        format_type=args.format_type
    )


if __name__ == "__main__":
    main()
