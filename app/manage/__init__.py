import argparse
import logging
import sys
import traceback

from app.logging import setup_logging
from rich.console import Console
from .status import cmd_status
from .reset import cmd_reset
from .seed import cmd_seed
from .fixtures import (
    cmd_clean_fixtures,
    cmd_demote_fixtures,
    cmd_fetch_fixtures,
    cmd_fetch_users_from_beatmapsets,
    cmd_fixture_status,
    cmd_generate,
    cmd_promote_fixtures,
    cmd_reconcile,
    cmd_refresh_archives,
    cmd_refresh_top_players,
)

def build_status_parser(subparsers):
    p = subparsers.add_parser("status", help="View database status")
    p.add_argument(
        "target",
        nargs="?",
        default="summary",
        choices=["summary", "users", "beatmaps", "beatmapsets", "queues", "requests"],
        help="Status target (default: summary)",
    )
    return p


def build_reset_parser(subparsers):
    p = subparsers.add_parser("reset", help="Reset database")
    p.add_argument(
        "seed_target",
        nargs="?",
        default=None,
        help="Optional seed target after reset (all, users, beatmaps, queues, requests)",
    )
    p.add_argument("--force", "-f", action="store_true", help="Skip confirmation prompt")
    return p


def build_seed_parser(subparsers):
    p = subparsers.add_parser("seed", help="Seed database")
    p.add_argument("target", help="Seed target (all, users, beatmaps, queues, requests)")
    p.add_argument(
        "--ensure-fixtures", action="store_true", help="Auto-fetch/generate missing fixtures"
    )
    p.add_argument("--profile", default="default", help="Profile name for fixture counts")
    return p


def build_fixtures_parser(subparsers):
    p = subparsers.add_parser("fixtures", help="Manage test fixtures")
    fixture_subparsers = p.add_subparsers(dest="fixture_command", required=True)

    # fixtures clean
    clean_p = fixture_subparsers.add_parser(
        "clean", help="Delete all fixture files and reset metadata"
    )
    clean_p.add_argument(
        "--clear-failed-ids", action="store_true", help="Clear failed IDs from Redis"
    )
    clean_p.add_argument(
        "--clear-top-player-ids", action="store_true", help="Clear top player IDs from metadata"
    )
    clean_p.add_argument(
        "--clear-promoted", action="store_true", help="Clear promoted fixture metadata"
    )
    clean_p.add_argument("--force", "-f", action="store_true", help="Skip confirmation prompt")

    # fixtures demote
    demote_p = fixture_subparsers.add_parser(
        "demote", help="Move promoted fixtures back to instance"
    )
    demote_p.add_argument("--beatmaps", action="store_true", help="Demote beatmaps")
    demote_p.add_argument("--beatmapsets", action="store_true", help="Demote beatmapsets")
    demote_p.add_argument("--users", action="store_true", help="Demote users")
    demote_p.add_argument("--scores", action="store_true", help="Demote scores")
    demote_p.add_argument("--beatmap-scores", action="store_true", help="Demote beatmap scores")
    demote_p.add_argument(
        "--beatmap-attributes", action="store_true", help="Demote beatmap attributes"
    )
    demote_p.add_argument("--queues", action="store_true", help="Demote queues")
    demote_p.add_argument("--requests", action="store_true", help="Demote requests")
    demote_p.add_argument("--force", "-f", action="store_true", help="Skip confirmation prompt")

    # fixtures fetch
    fetch_p = fixture_subparsers.add_parser("fetch", help="Fetch fixture data from the osu! API")
    fetch_p.add_argument(
        "--criteria",
        default="standard",
        choices=["minimal", "standard", "targeted", "search-test"],
        help="Fetch criteria (default: standard)",
    )
    fetch_p.add_argument(
        "--source",
        default="auto",
        choices=["auto", "archive", "top-players"],
        help="ID source (default: auto)",
    )
    fetch_p.add_argument("--beatmaps", type=int, default=0, help="Number of beatmaps to fetch")
    fetch_p.add_argument(
        "--beatmapsets", type=int, default=0, help="Number of beatmapsets to fetch"
    )
    fetch_p.add_argument("--users-osu", type=int, default=0, help="Number of osu! users to fetch")
    fetch_p.add_argument(
        "--users-taiko", type=int, default=0, help="Number of taiko users to fetch"
    )
    fetch_p.add_argument(
        "--users-fruits", type=int, default=0, help="Number of fruits users to fetch"
    )
    fetch_p.add_argument(
        "--users-mania", type=int, default=0, help="Number of mania users to fetch"
    )
    fetch_p.add_argument(
        "--scores-best", type=int, default=0, help="Number of best scores to fetch"
    )
    fetch_p.add_argument(
        "--scores-firsts", type=int, default=0, help="Number of first place scores to fetch"
    )
    fetch_p.add_argument(
        "--scores-recent", type=int, default=0, help="Number of recent scores to fetch"
    )
    fetch_p.add_argument(
        "--beatmap-scores", type=int, default=0, help="Number of beatmap scores to fetch"
    )
    fetch_p.add_argument(
        "--beatmap-attributes", type=int, default=0, help="Number of beatmap attributes to fetch"
    )
    fetch_p.add_argument("--status", nargs="+", help="Filter by status (for targeted criteria)")
    fetch_p.add_argument("--difficulty-range", help="Filter by difficulty (for targeted criteria)")
    fetch_p.add_argument("--playcount-range", help="Filter by playcount (for targeted criteria)")
    fetch_p.add_argument("--activity-tier", help="Filter by activity tier (for targeted criteria)")
    fetch_p.add_argument("--ruleset", nargs="+", help="Filter by ruleset (for targeted criteria)")
    fetch_p.add_argument(
        "--force-fetch", action="store_true", help="Force fetch even if recently fetched"
    )
    fetch_p.add_argument("--no-progress", action="store_true", help="Hide progress bar")
    fetch_p.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    fetch_p.add_argument(
        "--min-per-category", type=int, default=1, help="Min fixtures per category (search-test)"
    )
    fetch_p.add_argument(
        "--max-total", type=int, default=500, help="Max total API calls (search-test)"
    )
    fetch_p.add_argument("--gaps", action="store_true", help="Show coverage gaps (search-test)")
    fetch_p.add_argument("--full", action="store_true", help="Full coverage mode (search-test)")
    fetch_p.add_argument("--quick", action="store_true", help="Quick mode (search-test)")

    # fixtures fetch-users-from-beatmapsets
    fixture_subparsers.add_parser(
        "fetch-users-from-beatmapsets",
        help="Extract user IDs from beatmapset fixtures and fetch them",
    )

    # fixtures generate
    gen_p = fixture_subparsers.add_parser("generate", help="Generate queue and request fixtures")
    gen_p.add_argument(
        "--queue-count", type=int, default=10, help="Number of queues to generate (default: 10)"
    )
    gen_p.add_argument(
        "--request-count",
        type=int,
        default=100,
        help="Number of requests to generate (default: 100)",
    )

    # fixtures promote
    promote_p = fixture_subparsers.add_parser(
        "promote", help="Move instance fixtures to tests/fixtures/"
    )
    promote_p.add_argument("--beatmaps", action="store_true", help="Promote beatmaps")
    promote_p.add_argument("--beatmapsets", action="store_true", help="Promote beatmapsets")
    promote_p.add_argument("--users", action="store_true", help="Promote users")
    promote_p.add_argument("--scores", action="store_true", help="Promote scores")
    promote_p.add_argument("--beatmap-scores", action="store_true", help="Promote beatmap scores")
    promote_p.add_argument(
        "--beatmap-attributes", action="store_true", help="Promote beatmap attributes"
    )
    promote_p.add_argument("--queues", action="store_true", help="Promote queues")
    promote_p.add_argument("--requests", action="store_true", help="Promote requests")
    promote_p.add_argument("--force", "-f", action="store_true", help="Skip confirmation prompt")

    # fixtures reconcile
    reconcile_p = fixture_subparsers.add_parser(
        "reconcile", help="Reconcile fixture metadata with disk state"
    )
    reconcile_p.add_argument(
        "--category",
        "-c",
        choices=[
            "beatmaps",
            "beatmapsets",
            "users",
            "scores",
            "beatmap_scores",
            "beatmap_attributes",
        ],
        help="Specific category to reconcile",
    )
    reconcile_p.add_argument(
        "--dry-run", action="store_true", help="Show changes without applying them"
    )

    # fixtures refresh-archives
    refresh_archives_p = fixture_subparsers.add_parser(
        "refresh-archives", help="Refresh archive index from osu.sh"
    )
    refresh_archives_p.add_argument(
        "--force", "-f", action="store_true", help="Force refresh even if recently updated"
    )

    # fixtures refresh-top-players
    refresh_top_p = fixture_subparsers.add_parser(
        "refresh-top-players", help="Refresh top player IDs from osu! API"
    )
    refresh_top_p.add_argument("--rulesets", nargs="+", help="Rulesets to refresh (default: all)")
    refresh_top_p.add_argument(
        "--count", type=int, default=1000, help="Count per ruleset (default: 1000)"
    )

    # fixtures status
    status_p = fixture_subparsers.add_parser("status", help="Show fixture status")
    status_p.add_argument("--instance", action="store_true", help="Show only instance/ fixtures")
    status_p.add_argument("--promoted", action="store_true", help="Show only promoted fixtures")
    status_p.add_argument("--detailed", action="store_true", help="Include detailed file lists")
    status_p.add_argument("--gaps", action="store_true", help="Show missing fixture gaps")

    return p


# ruff: noqa: C901 PLC0415 F401
async def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_status_parser(subparsers)
    build_reset_parser(subparsers)
    build_seed_parser(subparsers)
    build_fixtures_parser(subparsers)

    args = parser.parse_args()

    verbose = getattr(args, "verbose", False)
    setup_logging(
        enabled_loggers=["manage", "database", "fixtures"],
        level_overrides={"database": logging.WARNING},
        no_debug=not verbose,
    )

    try:
        match args.command:
            case "status":
                await cmd_status(args.target)
            case "reset":
                await cmd_reset(args.seed_target, force=getattr(args, "force", False))
            case "seed":
                await cmd_seed(
                    args.target,
                    ensure_fixtures=getattr(args, "ensure_fixtures", False),
                    profile_name=getattr(args, "profile", "default"),
                )
            case "fixtures":
                fixture_cmd = args.fixture_command
                match fixture_cmd:
                    case "fetch":
                        from .fixtures.config import FetchConfig

                        fetch_config = FetchConfig(
                            criteria=args.criteria,
                            source=args.source,
                            beatmaps=args.beatmaps or 0,
                            beatmapsets=args.beatmapsets or 0,
                            users_osu=args.users_osu or 0,
                            users_taiko=args.users_taiko or 0,
                            users_fruits=args.users_fruits or 0,
                            users_mania=args.users_mania or 0,
                            scores_best=args.scores_best or 0,
                            scores_firsts=args.scores_firsts or 0,
                            scores_recent=args.scores_recent or 0,
                            beatmap_scores=args.beatmap_scores or 0,
                            beatmap_attributes=args.beatmap_attributes or 0,
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
                        await cmd_fetch_fixtures(fetch_config)
                    case "refresh-top-players":
                        await cmd_refresh_top_players(
                            rulesets=args.rulesets,
                            count=args.count,
                        )
                    case "status":
                        await cmd_fixture_status(
                            instance=getattr(args, "instance", False),
                            promoted=getattr(args, "promoted", False),
                            detailed=getattr(args, "detailed", False),
                            gaps=getattr(args, "gaps", False),
                        )
                    case "promote":
                        await cmd_promote_fixtures(
                            beatmaps=args.beatmaps,
                            beatmapsets=args.beatmapsets,
                            users=args.users,
                            scores=args.scores,
                            beatmap_scores=args.beatmap_scores,
                            beatmap_attributes=args.beatmap_attributes,
                            queues=getattr(args, "queues", False),
                            requests=getattr(args, "requests", False),
                            force=getattr(args, "force", False),
                        )
                    case "demote":
                        await cmd_demote_fixtures(
                            beatmaps=args.beatmaps,
                            beatmapsets=args.beatmapsets,
                            users=args.users,
                            scores=args.scores,
                            beatmap_scores=args.beatmap_scores,
                            beatmap_attributes=args.beatmap_attributes,
                            queues=getattr(args, "queues", False),
                            requests=getattr(args, "requests", False),
                            force=getattr(args, "force", False),
                        )
                    case "clean":
                        await cmd_clean_fixtures(
                            clear_failed_ids=args.clear_failed_ids,
                            clear_top_player_ids=args.clear_top_player_ids,
                            clear_promoted=args.clear_promoted,
                            force=getattr(args, "force", False),
                        )
                    case "refresh-archives":
                        await cmd_refresh_archives(
                            force=getattr(args, "force", False),
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
                    case "fetch-users-from-beatmapsets":
                        await cmd_fetch_users_from_beatmapsets()
    except Exception as e:
        from rich.console import Console

        console = Console()
        console.print(f"\n[red]❌ Error:[/red] {e}")
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise SystemExit(1) from None
