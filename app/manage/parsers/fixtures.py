"""Fixtures subcommand parser."""


def build_fixtures_parser(subparsers):
    """Build the parser for the 'fixtures' subcommand and all its sub-subcommands."""
    fixtures_parser = subparsers.add_parser("fixtures", help="Manage test fixtures")
    fixtures_subparsers = fixtures_parser.add_subparsers(dest="fixture_command", required=True)

    _build_fetch_parser(fixtures_subparsers)
    _build_fetch_users_from_beatmapsets_parser(fixtures_subparsers)
    _build_promote_parser(fixtures_subparsers)
    _build_demote_parser(fixtures_subparsers)
    _build_refresh_top_players_parser(fixtures_subparsers)
    _build_fixture_status_parser(fixtures_subparsers)
    _build_clean_parser(fixtures_subparsers)
    _build_refresh_archives_parser(fixtures_subparsers)
    _build_reconcile_parser(fixtures_subparsers)
    _build_generate_parser(fixtures_subparsers)

    return fixtures_parser


def _build_fetch_parser(fixtures_subparsers):
    """Build the parser for 'fixtures fetch'."""
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


def _build_fetch_users_from_beatmapsets_parser(fixtures_subparsers):
    """Build the parser for 'fixtures fetch-users-from-beatmapsets'."""
    fixtures_subparsers.add_parser(
        "fetch-users-from-beatmapsets",
        help="Extract user IDs from beatmapset fixtures and fetch those users",
        description=(
            "Reads beatmapset fixtures to extract unique owner user IDs,\n"
            "then fetches those users from the osu! API."
        ),
    )


def _build_promote_parser(fixtures_subparsers):
    """Build the parser for 'fixtures promote'."""
    p = fixtures_subparsers.add_parser("promote", help="Promote fixtures from instance to tests")
    p.add_argument("--force", "-f", action="store_true", help="Skip confirmation prompt")
    p.add_argument("--beatmaps", action="store_true", help="Promote beatmaps (all if none specified)")
    p.add_argument("--beatmapsets", action="store_true", help="Promote beatmapsets (all if none specified)")
    p.add_argument("--users", action="store_true", help="Promote users (all if none specified)")
    p.add_argument("--scores", action="store_true", help="Promote scores (all if none specified)")
    p.add_argument("--beatmap-scores", action="store_true", help="Promote beatmap scores (all if none specified)")
    p.add_argument("--beatmap-attributes", action="store_true", help="Promote beatmap attributes (all if none specified)")
    p.add_argument("--queues", action="store_true", help="Promote queues (all if none specified)")
    p.add_argument("--requests", action="store_true", help="Promote requests (all if none specified)")


def _build_demote_parser(fixtures_subparsers):
    """Build the parser for 'fixtures demote'."""
    p = fixtures_subparsers.add_parser("demote", help="Demote fixtures from tests to instance")
    p.add_argument("--force", "-f", action="store_true", help="Skip confirmation prompt")
    p.add_argument("--beatmaps", action="store_true", help="Demote beatmaps (all if none specified)")
    p.add_argument("--beatmapsets", action="store_true", help="Demote beatmapsets (all if none specified)")
    p.add_argument("--users", action="store_true", help="Demote users (all if none specified)")
    p.add_argument("--scores", action="store_true", help="Demote scores (all if none specified)")
    p.add_argument("--beatmap-scores", action="store_true", help="Demote beatmap scores (all if none specified)")
    p.add_argument("--beatmap-attributes", action="store_true", help="Demote beatmap attributes (all if none specified)")
    p.add_argument("--queues", action="store_true", help="Demote queues (all if none specified)")
    p.add_argument("--requests", action="store_true", help="Demote requests (all if none specified)")


def _build_refresh_top_players_parser(fixtures_subparsers):
    """Build the parser for 'fixtures refresh-top-players'."""
    p = fixtures_subparsers.add_parser("refresh-top-players", help="Fetch top players from osu! API")
    p.add_argument(
        "--ruleset", "-r",
        dest="rulesets",
        action="append",
        choices=["osu", "taiko", "fruits", "mania"],
        help="Ruleset to refresh (can be specified multiple times). If not provided, refreshes all rulesets.",
    )
    p.add_argument(
        "--count", "-c",
        type=int,
        default=1000,
        help="Number of player IDs to collect per ruleset (default: 1000)",
    )


def _build_fixture_status_parser(fixtures_subparsers):
    """Build the parser for 'fixtures status'."""
    p = fixtures_subparsers.add_parser("status", help="Show fixture status")
    p.add_argument("--instance", "-i", action="store_true", help="Show only instance/ fixtures")
    p.add_argument("--promoted", "-p", action="store_true", help="Show only tests/fixtures/ promoted fixtures")
    p.add_argument("--detailed", "-d", action="store_true", help="Include detailed file lists")
    p.add_argument("--gaps", "-g", action="store_true", help="Show missing fixture gaps (only for promoted)")


def _build_clean_parser(fixtures_subparsers):
    """Build the parser for 'fixtures clean'."""
    p = fixtures_subparsers.add_parser("clean", help="Delete all fixtures")
    p.add_argument("--force", "-f", action="store_true", help="Skip confirmation prompt")
    p.add_argument("--clear-failed-ids", action="store_true", help="Also clear failed IDs from metadata")
    p.add_argument("--clear-top-player-ids", action="store_true", help="Also clear top player IDs from metadata")
    p.add_argument(
        "--clear-promoted",
        action="store_true",
        help="Also clear promoted fixture metadata (WARNING: will cause metadata desync if fixture files remain)",
    )


def _build_refresh_archives_parser(fixtures_subparsers):
    """Build the parser for 'fixtures refresh-archives'."""
    p = fixtures_subparsers.add_parser("refresh-archives", help="Refresh archive index from osu.sh")
    p.add_argument("--force", "-f", action="store_true", help="Force refresh even if recently updated")


def _build_reconcile_parser(fixtures_subparsers):
    """Build the parser for 'fixtures reconcile'."""
    p = fixtures_subparsers.add_parser(
        "reconcile",
        help="Reconcile fixture metadata counts with actual disk state"
    )
    p.add_argument(
        "--category", "-c",
        choices=["beatmaps", "beatmapsets", "users", "scores", "beatmap_scores", "beatmap_attributes"],
        help="Specific category to reconcile"
    )
    p.add_argument("--dry-run", action="store_true", help="Show changes without applying them")


def _build_generate_parser(fixtures_subparsers):
    """Build the parser for 'fixtures generate'."""
    p = fixtures_subparsers.add_parser(
        "generate",
        help="Generate diverse queue and request fixtures for testing"
    )
    p.add_argument(
        "--queue-count",
        type=int,
        default=10,
        help="Number of queues to generate (default: 10)",
    )
    p.add_argument(
        "--request-count",
        type=int,
        default=100,
        help="Number of requests to generate (default: 100)",
    )
