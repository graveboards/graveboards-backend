import argparse
import asyncio
import logging
import sys

from app.logging import setup_logging
from .status import cmd_status
from .reset import cmd_reset
from .seed import cmd_seed
from .fixtures import (
    cmd_fetch_fixtures,
    cmd_fixture_status,
    cmd_promote_fixtures,
    cmd_demote_fixtures,
    cmd_clean_fixtures,
    cmd_refresh_top_players,
    cmd_refresh_archives,
    cmd_reconcile,
    cmd_generate,
    cmd_fetch_users_from_beatmapsets,
)
from .parsers import (
    build_status_parser,
    build_reset_parser,
    build_seed_parser,
    build_fixtures_parser,
)


async def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_status_parser(subparsers)
    build_reset_parser(subparsers)
    build_seed_parser(subparsers)
    build_fixtures_parser(subparsers)

    args = parser.parse_args()

    verbose = getattr(args, 'verbose', False)
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
                await cmd_seed(
                    args.target,
                    ensure_fixtures=getattr(args, 'ensure_fixtures', False),
                    profile_name=getattr(args, 'profile', 'default'),
                )
            case "fixtures":
                match args.fixture_command:
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
                    case "clean":
                        await cmd_clean_fixtures(
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
                    case "fetch-users-from-beatmapsets":
                        await cmd_fetch_users_from_beatmapsets()
    except Exception as e:
        import traceback
        from rich.console import Console
        console = Console()
        console.print(f"\n[red]❌ Error:[/red] {e}")
        console.print("[dim]" + traceback.format_exc() + "[/dim]")
        raise SystemExit(1)
