import argparse
import logging

from app.database.status import STATUS_TARGETS
from app.database.seeding import SeedTarget
from app.logging import setup_logging
from .status import cmd_status
from .reset import cmd_reset
from .seed import cmd_seed
from .fixtures import (
    cmd_fetch_fixtures,
    cmd_list_fixtures,
    cmd_validate_fixtures,
    cmd_promote_fixtures,
    cmd_demote_fixtures,
    cmd_wipe_fixtures,
    cmd_refresh_top_players,
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

    fetch_parser = fixtures_subparsers.add_parser("fetch", help="Fetch fresh fixture data from osu! API")
    fetch_parser.add_argument(
        "--scale", "-s",
        type=float,
        default=1.0,
        help="Scale factor for sample counts (default: 1.0)",
    )
    fetch_parser.add_argument(
        "--minimal",
        action="store_true",
        help="Use minimal profile (1 of each type)",
    )
    fetch_parser.add_argument(
        "--beatmaps",
        type=int,
        help="Number of beatmaps to fetch",
    )
    fetch_parser.add_argument(
        "--beatmapsets",
        type=int,
        help="Number of beatmapsets to fetch",
    )
    fetch_parser.add_argument(
        "--users-osu",
        type=int,
        help="Number of osu! users to fetch",
    )
    fetch_parser.add_argument(
        "--users-taiko",
        type=int,
        help="Number of taiko users to fetch",
    )
    fetch_parser.add_argument(
        "--users-fruits",
        type=int,
        help="Number of fruits users to fetch",
    )
    fetch_parser.add_argument(
        "--users-mania",
        type=int,
        help="Number of mania users to fetch",
    )
    fetch_parser.add_argument(
        "--scores-best",
        type=int,
        help="Number of best scores to fetch",
    )
    fetch_parser.add_argument(
        "--scores-firsts",
        type=int,
        help="Number of firsts scores to fetch",
    )
    fetch_parser.add_argument(
        "--scores-recent",
        type=int,
        help="Number of recent scores to fetch",
    )
    fetch_parser.add_argument(
        "--beatmap-scores",
        type=int,
        help="Number of beatmap scores to fetch",
    )
    fetch_parser.add_argument(
        "--beatmap-attributes",
        type=int,
        help="Number of beatmap attributes to fetch",
    )
    fetch_parser.add_argument(
        "--beatmaps-range-min",
        type=int,
        help="Minimum beatmap ID to fetch",
    )
    fetch_parser.add_argument(
        "--beatmaps-range-max",
        type=int,
        help="Maximum beatmap ID to fetch",
    )
    fetch_parser.add_argument(
        "--beatmapsets-range-min",
        type=int,
        help="Minimum beatmapset ID to fetch",
    )
    fetch_parser.add_argument(
        "--beatmapsets-range-max",
        type=int,
        help="Maximum beatmapset ID to fetch",
    )
    fetch_parser.add_argument(
        "--users-range-min",
        type=int,
        help="Minimum user ID to fetch",
    )
    fetch_parser.add_argument(
        "--users-range-max",
        type=int,
        help="Maximum user ID to fetch",
    )
    fetch_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose/debug logging",
    )

    promote_parser = fixtures_subparsers.add_parser("promote", help="Promote fixtures from instance to tests")
    promote_parser.add_argument("--beatmaps", action="store_true", help="Promote beatmaps (all if none specified)")
    promote_parser.add_argument("--beatmapsets", action="store_true",
                                help="Promote beatmapsets (all if none specified)")
    promote_parser.add_argument("--users", action="store_true", help="Promote users (all if none specified)")
    promote_parser.add_argument("--scores", action="store_true", help="Promote scores (all if none specified)")
    promote_parser.add_argument("--beatmap-scores", action="store_true",
                                help="Promote beatmap scores (all if none specified)")
    promote_parser.add_argument("--beatmap-attributes", action="store_true",
                                help="Promote beatmap attributes (all if none specified)")

    demote_parser = fixtures_subparsers.add_parser("demote", help="Demote fixtures from tests to instance")
    demote_parser.add_argument("--beatmaps", action="store_true", help="Demote beatmaps (all if none specified)")
    demote_parser.add_argument("--beatmapsets", action="store_true", help="Demote beatmapsets (all if none specified)")
    demote_parser.add_argument("--users", action="store_true", help="Demote users (all if none specified)")
    demote_parser.add_argument("--scores", action="store_true", help="Demote scores (all if none specified)")
    demote_parser.add_argument("--beatmap-scores", action="store_true",
                               help="Demote beatmap scores (all if none specified)")
    demote_parser.add_argument("--beatmap-attributes", action="store_true",
                               help="Demote beatmap attributes (all if none specified)")
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

    wipe_parser = fixtures_subparsers.add_parser("wipe", help="Delete all fixtures")
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

    args = parser.parse_args()

    no_debug = not getattr(args, 'verbose', False)
    setup_logging(
        enabled_loggers=["manage", "database"],
        level_overrides={"database": logging.WARNING},
        no_debug=no_debug
    )

    match args.command:
        case "status":
            await cmd_status(args.target)
        case "reset":
            await cmd_reset(args.seed_target)
        case "seed":
            await cmd_seed(args.target)
        case "fixtures":
            match args.fixture_command:
                case "fetch":
                    await cmd_fetch_fixtures(
                        scale=args.scale,
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
                        use_minimal=args.minimal,
                        beatmaps_range_min=args.beatmaps_range_min,
                        beatmaps_range_max=args.beatmaps_range_max,
                        beatmapsets_range_min=args.beatmapsets_range_min,
                        beatmapsets_range_max=args.beatmapsets_range_max,
                        users_range_min=args.users_range_min,
                        users_range_max=args.users_range_max,
                    )
                case "refresh-top-players":
                    await cmd_refresh_top_players(
                        rulesets=args.rulesets,
                        count=args.count,
                    )
                case "list":
                    await cmd_list_fixtures()
                case "validate":
                    await cmd_validate_fixtures()
                case "promote":
                    await cmd_promote_fixtures(
                        beatmaps=args.beatmaps,
                        beatmapsets=args.beatmapsets,
                        users=args.users,
                        scores=args.scores,
                        beatmap_scores=args.beatmap_scores,
                        beatmap_attributes=args.beatmap_attributes,
                    )
                case "demote":
                    await cmd_demote_fixtures(
                        beatmaps=args.beatmaps,
                        beatmapsets=args.beatmapsets,
                        users=args.users,
                        scores=args.scores,
                        beatmap_scores=args.beatmap_scores,
                        beatmap_attributes=args.beatmap_attributes,
                    )
                case "wipe":
                    await cmd_wipe_fixtures(
                        clear_failed_ids=args.clear_failed_ids,
                        clear_top_player_ids=args.clear_top_player_ids,
                        clear_promoted=args.clear_promoted,
                    )
