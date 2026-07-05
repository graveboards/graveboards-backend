import argparse
import asyncio
import logging
import sys

from app.database.status import STATUS_TARGETS
from app.database.seeding import SeedTarget
from app.logging import setup_logging
from .status import cmd_status
from .reset import cmd_reset
from .seed import cmd_seed
from .fixtures import (
    cmd_fetch_fixtures,
    cmd_fixture_status,
    cmd_promote_fixtures,
    cmd_demote_fixtures,
    cmd_wipe_fixtures,
    cmd_refresh_top_players,
    cmd_refresh_archives,
    cmd_reconcile,
    cmd_generate,
)


async def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status", help="View database status")
    status_parser.add_argument(
        "target",
        metavar="target",
        nargs="?",
        default="summary",
        choices=STATUS_TARGETS,
        help=f"What to show status for ({", ".join(STATUS_TARGETS)})"
    )

    reset_parser = subparsers.add_parser("reset", help="Reset database")
    reset_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Skip confirmation prompt",
    )
    reset_parser.add_argument(
        "--seed", "-s",
        dest="seed_target",
        metavar="target",
        nargs="?",
        const=SeedTarget.ALL,
        type=SeedTarget,
        choices=list(SeedTarget),
        help="Seed after reset (optionally specify target)"
    )

    seed_parser = subparsers.add_parser("seed", help="Seed database")
    seed_parser.add_argument(
        "target",
        metavar="target",
        type=SeedTarget,
        choices=list(SeedTarget),
        default=SeedTarget.ALL,
        help=f"What to seed in the database ({", ".join(SeedTarget)})"
    )

    fixtures_parser = subparsers.add_parser("fixtures", help="Manage test fixtures")
    fixtures_subparsers = fixtures_parser.add_subparsers(dest="fixture_command", required=True)

    fetch_parser = fixtures_subparsers.add_parser(
        "fetch",
        help="Fetch fixture data from osu! API",
        description=(
            "Fetch fixtures with two orthogonal dimensions:\n"
            "  --criteria: what variety to achieve (minimal, standard, targeted, search-test)\n"
            "  --source: where to get IDs (auto, archive, top-players)"
        ),
    )
    fetch_parser.add_argument(
        "--criteria",
        choices=["minimal", "standard", "targeted", "search-test"],
        default="standard",
        help="Coverage criteria (default: standard)",
    )
    fetch_parser.add_argument(
        "--source",
        choices=["auto", "archive", "top-players"],
        default="auto",
        help="ID source priority (default: auto)",
    )
    fetch_parser.add_argument(
        "--beatmaps", type=int, help="Number of beatmaps to fetch"
    )
    fetch_parser.add_argument(
        "--beatmapsets", type=int, help="Number of beatmapsets to fetch"
    )
    fetch_parser.add_argument(
        "--users-osu", type=int, help="Number of osu! users to fetch"
    )
    fetch_parser.add_argument(
        "--users-taiko", type=int, help="Number of taiko users to fetch"
    )
    fetch_parser.add_argument(
        "--users-fruits", type=int, help="Number of fruits users to fetch"
    )
    fetch_parser.add_argument(
        "--users-mania", type=int, help="Number of mania users to fetch"
    )
    fetch_parser.add_argument(
        "--scores-best", type=int, help="Number of best scores to fetch"
    )
    fetch_parser.add_argument(
        "--scores-firsts", type=int, help="Number of firsts scores to fetch"
    )
    fetch_parser.add_argument(
        "--scores-recent", type=int, help="Number of recent scores to fetch"
    )
    fetch_parser.add_argument(
        "--beatmap-scores", type=int, help="Number of beatmap scores to fetch"
    )
    fetch_parser.add_argument(
        "--beatmap-attributes", type=int, help="Number of beatmap attributes to fetch"
    )
    fetch_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose/debug logging"
    )
    fetch_parser.add_argument(
        "--no-progress", action="store_true", help="Disable progress bar display"
    )
    fetch_parser.add_argument(
        "--force-fetch",
        action="store_true",
        help="Force fetching until all counts are met (removes retry limits)",
    )
    fetch_parser.add_argument(
        "--fixtures-dir",
        type=str,
        default=None,
        help="Custom directory for fixture files and metadata (default: instance/fixtures/)",
    )

    targeted_group = fetch_parser.add_argument_group("targeted overrides")
    targeted_group.add_argument(
        "--status",
        action="append",
        metavar="STATUS",
        choices=["ranked", "loved", "qualified", "graveyard", "pending", "approved"],
        help="Fetch beatmapsets by status (--criteria targeted)",
    )
    targeted_group.add_argument(
        "--difficulty-range",
        type=str,
        metavar="RANGE",
        choices=["easy", "medium", "hard", "expert"],
        help="Fetch beatmaps by difficulty range (--criteria targeted)",
    )
    targeted_group.add_argument(
        "--playcount-range",
        type=str,
        metavar="RANGE",
        choices=["low", "medium", "high"],
        help="Fetch beatmaps by playcount range (--criteria targeted)",
    )
    targeted_group.add_argument(
        "--activity-tier",
        type=str,
        metavar="TIER",
        choices=["active", "moderate", "inactive"],
        help="Fetch users by activity tier (--criteria targeted)",
    )
    targeted_group.add_argument(
        "--ruleset",
        action="append",
        metavar="RULESET",
        choices=["osu", "taiko", "fruits", "mania"],
        help="Ruleset for targeted fetching (--criteria targeted)",
    )

    search_group = fetch_parser.add_argument_group("search-test overrides")
    search_group.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: --min-per-category=1 --max-total=20 (--criteria search-test)",
    )
    search_group.add_argument(
        "--min-per-category",
        type=int,
        default=1,
        help="Minimum items per coverage bucket (--criteria search-test)",
    )
    search_group.add_argument(
        "--max-total",
        type=int,
        default=500,
        help="Maximum total API calls before stopping (--criteria search-test)",
    )
    search_group.add_argument(
        "--gaps", action="store_true", help="Only show coverage gaps, don't fetch"
    )
    search_group.add_argument(
        "--full", action="store_true", help="Ignore metadata, fetch everything from scratch"
    )

    promote_parser = fixtures_subparsers.add_parser("promote", help="Promote fixtures from instance to tests")
    promote_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Skip confirmation prompt",
    )
    promote_parser.add_argument("--beatmaps", action="store_true", help="Promote beatmaps (all if none specified)")
    promote_parser.add_argument("--beatmapsets", action="store_true",
                                help="Promote beatmapsets (all if none specified)")
    promote_parser.add_argument("--users", action="store_true", help="Promote users (all if none specified)")
    promote_parser.add_argument("--scores", action="store_true", help="Promote scores (all if none specified)")
    promote_parser.add_argument("--beatmap-scores", action="store_true",
                                help="Promote beatmap scores (all if none specified)")
    promote_parser.add_argument("--beatmap-attributes", action="store_true",
                                help="Promote beatmap attributes (all if none specified)")
    promote_parser.add_argument("--queues", action="store_true", help="Promote queues (all if none specified)")
    promote_parser.add_argument("--requests", action="store_true", help="Promote requests (all if none specified)")

    demote_parser = fixtures_subparsers.add_parser("demote", help="Demote fixtures from tests to instance")
    demote_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Skip confirmation prompt",
    )
    demote_parser.add_argument("--beatmaps", action="store_true", help="Demote beatmaps (all if none specified)")
    demote_parser.add_argument("--beatmapsets", action="store_true", help="Demote beatmapsets (all if none specified)")
    demote_parser.add_argument("--users", action="store_true", help="Demote users (all if none specified)")
    demote_parser.add_argument("--scores", action="store_true", help="Demote scores (all if none specified)")
    demote_parser.add_argument("--beatmap-scores", action="store_true",
                               help="Demote beatmap scores (all if none specified)")
    demote_parser.add_argument("--beatmap-attributes", action="store_true",
                               help="Demote beatmap attributes (all if none specified)")
    demote_parser.add_argument("--queues", action="store_true", help="Demote queues (all if none specified)")
    demote_parser.add_argument("--requests", action="store_true", help="Demote requests (all if none specified)")
    refresh_parser = fixtures_subparsers.add_parser("refresh-top-players", help="Fetch top players from osu! API")
    refresh_parser.add_argument(
        "--ruleset", "-r",
        dest="rulesets",
        action="append",
        choices=["osu", "taiko", "fruits", "mania"],
        help="Ruleset to refresh (can be specified multiple times). If not provided, refreshes all rulesets.",
    )
    refresh_parser.add_argument(
        "--count", "-c",
        type=int,
        default=1000,
        help="Number of player IDs to collect per ruleset (default: 1000)",
    )

    status_parser = fixtures_subparsers.add_parser("status", help="Show fixture status")
    status_parser.add_argument(
        "--instance", "-i",
        action="store_true",
        help="Show only instance/ fixtures"
    )
    status_parser.add_argument(
        "--promoted", "-p",
        action="store_true",
        help="Show only tests/fixtures/ promoted fixtures"
    )
    status_parser.add_argument(
        "--detailed", "-d",
        action="store_true",
        help="Include detailed file lists"
    )
    status_parser.add_argument(
        "--gaps", "-g",
        action="store_true",
        help="Show missing fixture gaps (only for promoted)"
    )

    wipe_parser = fixtures_subparsers.add_parser("wipe", help="Delete all fixtures")
    wipe_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Skip confirmation prompt",
    )
    wipe_parser.add_argument(
        "--clear-failed-ids",
        action="store_true",
        help="Also clear failed IDs from metadata",
    )
    wipe_parser.add_argument(
        "--clear-top-player-ids",
        action="store_true",
        help="Also clear top player IDs from metadata",
    )
    wipe_parser.add_argument(
        "--clear-promoted",
        action="store_true",
        help="Also clear promoted fixture metadata (WARNING: will cause metadata desync if fixture files remain)",
    )

    refresh_archives_parser = fixtures_subparsers.add_parser("refresh-archives", help="Refresh archive index from osu.sh")
    refresh_archives_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force refresh even if recently updated"
    )

    reconcile_parser = fixtures_subparsers.add_parser(
        "reconcile",
        help="Reconcile fixture metadata counts with actual disk state"
    )
    reconcile_parser.add_argument(
        "--category", "-c",
        choices=["beatmaps", "beatmapsets", "users", "scores", "beatmap_scores", "beatmap_attributes"],
        help="Specific category to reconcile"
    )
    reconcile_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without applying them"
    )

    generate_parser = fixtures_subparsers.add_parser(
        "generate",
        help="Generate diverse queue and request fixtures for testing"
    )
    generate_parser.add_argument(
        "--queue-count",
        type=int,
        default=50,
        help="Number of queues to generate (default: 50)",
    )
    generate_parser.add_argument(
        "--request-count",
        type=int,
        default=100,
        help="Number of requests to generate (default: 100)",
    )

    args = parser.parse_args()

    verbose = getattr(args, 'verbose', False) or '-v' in sys.argv or '--verbose' in sys.argv
    no_debug = not verbose
    setup_logging(
        enabled_loggers=["manage", "database", "fixtures"],
        level_overrides={"database": logging.WARNING},
        no_debug=no_debug
    )

    try:
        match args.command:
            case "status":
                await cmd_status(args.target)
            case "reset":
                await cmd_reset(args.seed_target, force=getattr(args, 'force', False))
            case "seed":
                await cmd_seed(args.target)
            case "fixtures":
                match args.fixture_command:
                    case "fetch":
                        await cmd_fetch_fixtures(
                            criteria=args.criteria,
                            source=args.source,
                            beatmaps=args.beatmaps,
                            beatmapsets=args.beatmapsets,
                            users_osu=args.users_osu,
                            users_taiko=args.users_taiko,
                            users_fruits=args.users_fruits,
                            users_mania=args.users_mania,
                            scores_best=args.scores_best,
                            scores_firsts=args.scores_firsts,
                            scores_recent=args.scores_recent,
                            beatmap_scores=args.beatmap_scores,
                            beatmap_attributes=args.beatmap_attributes,
                            status=args.status,
                            difficulty_range=args.difficulty_range,
                            playcount_range=args.playcount_range,
                            activity_tier=args.activity_tier,
                            rulesets=args.ruleset,
                            force_fetch=args.force_fetch,
                            no_progress=args.no_progress,
                            verbose=args.verbose,
                            min_per_category=args.min_per_category,
                            max_total=args.max_total,
                            gaps=args.gaps,
                            full=args.full,
                            quick=args.quick,
                        )
                    case "refresh-top-players":
                        await cmd_refresh_top_players(
                            rulesets=args.rulesets,
                            count=args.count,
                        )
                    case "status":
                        await cmd_fixture_status(
                            instance=getattr(args, 'instance', False),
                            promoted=getattr(args, 'promoted', False),
                            detailed=getattr(args, 'detailed', False),
                            gaps=getattr(args, 'gaps', False),
                        )

                    case "promote":
                        await cmd_promote_fixtures(
                            beatmaps=args.beatmaps,
                            beatmapsets=args.beatmapsets,
                            users=args.users,
                            scores=args.scores,
                            beatmap_scores=args.beatmap_scores,
                            beatmap_attributes=args.beatmap_attributes,
                            queues=getattr(args, 'queues', False),
                            requests=getattr(args, 'requests', False),
                            force=getattr(args, 'force', False),
                        )
                    case "demote":
                        await cmd_demote_fixtures(
                            beatmaps=args.beatmaps,
                            beatmapsets=args.beatmapsets,
                            users=args.users,
                            scores=args.scores,
                            beatmap_scores=args.beatmap_scores,
                            beatmap_attributes=args.beatmap_attributes,
                            queues=getattr(args, 'queues', False),
                            requests=getattr(args, 'requests', False),
                            force=getattr(args, 'force', False),
                        )
                    case "wipe":
                        await cmd_wipe_fixtures(
                            clear_failed_ids=args.clear_failed_ids,
                            clear_top_player_ids=args.clear_top_player_ids,
                            clear_promoted=args.clear_promoted,
                            force=getattr(args, 'force', False),
                        )
                    case "refresh-archives":
                        await cmd_refresh_archives(
                            force=getattr(args, 'force', False),
                        )
                    case "reconcile":
                        await cmd_reconcile(
                            category=args.category,
                            dry_run=args.dry_run,
                        )
                    case "generate":
                        await cmd_generate(
                            queue_count=args.queue_count,
                            request_count=args.request_count,
                        )
    except Exception as e:
        import traceback
        from rich.console import Console
        console = Console()
        console.print(f"\n[red]❌ Error:[/red] {e}")
        console.print("[dim]" + traceback.format_exc() + "[/dim]")
        raise SystemExit(1)
