"""Display utilities for fixture operations."""

from rich.console import Console
from rich.table import Table

console = Console()


def print_coverage_gaps(fetcher) -> None:
    """Print coverage gaps from metadata.json."""
    console.print("[bold]Coverage status from metadata.json:[/bold]")

    search_cov = fetcher.metadata.get("search_test_coverage", {})
    if not search_cov:
        console.print("  [yellow]No previous coverage data found.[/yellow]")
        console.print("  Will fetch all buckets from scratch.")
        return

    last_updated = search_cov.get("last_updated", "unknown")
    console.print(f"  Last updated: {last_updated}")
    console.print()

    gap_items = []
    full_items = []

    genres = search_cov.get("beatmapset_genres", [])
    if genres:
        sample = ", ".join(str(g) for g in genres[:5])
        full_items.append(f"genres ({len(genres)} total)")
        if len(genres) > 5:
            full_items.append(f"    samples: {sample}, ...")
        else:
            full_items.append(f"    values: {sample}")
    else:
        gap_items.append("beatmapset_genres")

    langs = search_cov.get("beatmapset_languages", [])
    if langs:
        sample = ", ".join(str(l) for l in langs[:5])
        full_items.append(f"languages ({len(langs)} total)")
        if len(langs) > 5:
            full_items.append(f"    samples: {sample}, ...")
        else:
            full_items.append(f"    values: {sample}")
    else:
        gap_items.append("beatmapset_languages")

    nsfw_true = search_cov.get("beatmapset_nsfw_true_ids", [])
    nsfw_false = search_cov.get("beatmapset_nsfw_false_ids", [])
    if nsfw_true and nsfw_false:
        full_items.append(f"nsfw (true: {len(nsfw_true)}, false: {len(nsfw_false)})")
    else:
        if not nsfw_true:
            gap_items.append("nsfw=true")
        if not nsfw_false:
            gap_items.append("nsfw=false")

    modes = search_cov.get("beatmap_modes", [])
    if modes:
        full_items.append(f"beatmap_modes ({len(modes)} total)")
        full_items.append(f"    values: {', '.join(str(m) for m in modes)}")
    else:
        gap_items.append("beatmap_modes")

    countries = search_cov.get("country_codes", [])
    if countries:
        full_items.append(f"countries ({len(countries)} total)")
        if len(countries) > 5:
            full_items.append(f"    samples: {', '.join(countries[:5])}, ...")
        else:
            full_items.append(f"    values: {', '.join(countries)}")
    else:
        gap_items.append("country_codes")

    restr = search_cov.get("restricted_users", {})
    restr_true = restr.get("true_ids", [])
    restr_false = restr.get("false_ids", [])
    if restr_true and restr_false:
        full_items.append(f"restricted (true: {len(restr_true)}, false: {len(restr_false)})")
    else:
        if not restr_true:
            gap_items.append("restricted=true")
        if not restr_false:
            gap_items.append("restricted=false")

    statuses = search_cov.get("beatmapset_statuses", [])
    if statuses:
        full_items.append(f"statuses ({len(statuses)} total)")
        if len(statuses) > 5:
            full_items.append(f"    samples: {', '.join(statuses[:5])}, ...")
        else:
            full_items.append(f"    values: {', '.join(statuses)}")
    else:
        gap_items.append("beatmapset_statuses")

    if full_items:
        console.print("  [green]Covered:[/green]")
        for item in full_items:
            console.print(f"    {item}")

    if gap_items:
        console.print("  [yellow]Gaps:[/yellow]")
        for item in gap_items:
            console.print(f"    - {item}")

    if not gap_items:
        console.print("\n  [green]All major buckets covered![/green]")


def print_coverage_report(coverage: dict) -> None:
    """Print the full coverage report as a table."""
    console.print("\n[bold]Search test fixture coverage:[/bold]")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Category")
    table.add_column("Status")
    table.add_column("Details")

    _add_row(
        table,
        "Beatmapset Genres",
        "OK" if coverage.get("beatmapset_genres") else "MISSING",
        str(len(coverage.get("beatmapset_genres", {}))),
    )
    _add_row(
        table,
        "Beatmapset Languages",
        "OK" if coverage.get("beatmapset_languages") else "MISSING",
        str(len(coverage.get("beatmapset_languages", {}))),
    )
    nsfw = coverage.get("beatmapset_nsfw", {})
    _add_row(
        table,
        "Beatmapset NSFW",
        (
            "OK"
            if nsfw.get("true", {}).get("count", 0) > 0
            and nsfw.get("false", {}).get("count", 0) > 0
            else "PARTIAL"
        ),
        f"true:{nsfw.get('true', {}).get('count', 0)}, false:{nsfw.get('false', {}).get('count', 0)}",
    )
    _add_row(
        table,
        "Beatmapset Statuses",
        "OK" if coverage.get("beatmapset_statuses") else "MISSING",
        str(len(coverage.get("beatmapset_statuses", []))),
    )
    _add_row(
        table,
        "Beatmapset Ratings",
        (
            "OK"
            if any(
                coverage.get("beatmapset_ratings", {}).get(c, {}).get("count", 0) > 0
                for c in ("low", "medium", "high")
            )
            else "MISSING"
        ),
        ", ".join(
            f"{c}:{coverage.get('beatmapset_ratings', {}).get(c, {}).get('count', 0)}"
            for c in ("low", "medium", "high")
        ),
    )
    _add_row(
        table,
        "Beatmapset Favourites",
        (
            "OK"
            if any(
                coverage.get("beatmapset_favourite_counts", {}).get(c, {}).get("count", 0) > 0
                for c in ("low", "medium", "high")
            )
            else "MISSING"
        ),
        ", ".join(
            f"{c}:{coverage.get('beatmapset_favourite_counts', {}).get(c, {}).get('count', 0)}"
            for c in ("low", "medium", "high")
        ),
    )
    _add_row(
        table,
        "Beatmapset Play Counts",
        (
            "OK"
            if any(
                coverage.get("beatmapset_play_counts", {}).get(c, {}).get("count", 0) > 0
                for c in ("low", "medium", "high")
            )
            else "MISSING"
        ),
        ", ".join(
            f"{c}:{coverage.get('beatmapset_play_counts', {}).get(c, {}).get('count', 0)}"
            for c in ("low", "medium", "high")
        ),
    )
    _add_row(
        table,
        "Beatmapset Has Description",
        "OK" if coverage.get("beatmapset_has_description") else "MISSING",
        "",
    )
    _add_row(
        table,
        "Beatmapset Has Pack Tags",
        "OK" if coverage.get("beatmapset_has_pack_tags") else "MISSING",
        "",
    )
    _add_row(
        table, "Beatmapset Video", "OK" if coverage.get("beatmapset_videos") else "MISSING", ""
    )
    _add_row(
        table,
        "Beatmapset Storyboard",
        "OK" if coverage.get("beatmapset_storyboards") else "MISSING",
        "",
    )
    _add_row(table, "Beatmapset Hype", "OK" if coverage.get("beatmapset_hype") else "MISSING", "")
    _add_row(
        table,
        "Beatmapset Nominations",
        "OK" if coverage.get("beatmapset_nominations") else "MISSING",
        "",
    )
    _add_row(
        table, "Beatmapset SR Gaps", "OK" if coverage.get("beatmapset_sr_gaps") else "MISSING", ""
    )
    _add_row(
        table,
        "Beatmapset Hit Lengths",
        "OK" if coverage.get("beatmapset_hit_lengths") else "MISSING",
        "",
    )

    bm_modes = coverage.get("beatmap_modes", {})
    _add_row(table, "Beatmap Modes", "OK" if bm_modes else "MISSING", str(len(bm_modes)))
    bm_diffs = coverage.get("beatmap_difficulties", {})
    _add_row(
        table,
        "Beatmap Difficulties",
        (
            "OK"
            if any(
                bm_diffs.get(c, {}).get("count", 0) > 0
                for c in ("easy", "medium", "hard", "expert")
            )
            else "MISSING"
        ),
        ", ".join(
            f"{c}:{bm_diffs.get(c, {}).get('count', 0)}"
            for c in ("easy", "medium", "hard", "expert")
        ),
    )
    bm_pc = coverage.get("beatmap_playcounts", {})
    _add_row(
        table,
        "Beatmap Playcounts",
        (
            "OK"
            if any(bm_pc.get(c, {}).get("count", 0) > 0 for c in ("low", "medium", "high"))
            else "MISSING"
        ),
        ", ".join(f"{c}:{bm_pc.get(c, {}).get('count', 0)}" for c in ("low", "medium", "high")),
    )
    _add_row(
        table,
        "Beatmap BPM",
        (
            "OK"
            if any(
                coverage.get("beatmap_bpm", {}).get(c, {}).get("count", 0) > 0
                for c in ("low", "medium", "high")
            )
            else "MISSING"
        ),
        ", ".join(
            f"{c}:{coverage.get('beatmap_bpm', {}).get(c, {}).get('count', 0)}"
            for c in ("low", "medium", "high")
        ),
    )
    _add_row(
        table,
        "Beatmap Accuracy",
        (
            "OK"
            if any(
                coverage.get("beatmap_accuracy", {}).get(c, {}).get("count", 0) > 0
                for c in ("low", "medium", "high")
            )
            else "MISSING"
        ),
        ", ".join(
            f"{c}:{coverage.get('beatmap_accuracy', {}).get(c, {}).get('count', 0)}"
            for c in ("low", "medium", "high")
        ),
    )
    _add_row(
        table,
        "Beatmap Versions",
        "OK" if coverage.get("beatmap_versions") else "MISSING",
        str(len(coverage.get("beatmap_versions", []))),
    )
    _add_row(
        table,
        "Beatmap Max Combos",
        (
            "OK"
            if any(
                coverage.get("beatmap_max_combos", {}).get(c, {}).get("count", 0) > 0
                for c in ("low", "medium", "high")
            )
            else "MISSING"
        ),
        ", ".join(
            f"{c}:{coverage.get('beatmap_max_combos', {}).get(c, {}).get('count', 0)}"
            for c in ("low", "medium", "high")
        ),
    )
    _add_row(
        table,
        "Beatmap Drain",
        (
            "OK"
            if any(
                coverage.get("beatmap_drain", {}).get(c, {}).get("count", 0) > 0
                for c in ("low", "medium", "high")
            )
            else "MISSING"
        ),
        ", ".join(
            f"{c}:{coverage.get('beatmap_drain', {}).get(c, {}).get('count', 0)}"
            for c in ("low", "medium", "high")
        ),
    )
    _add_row(
        table,
        "Beatmap AR",
        (
            "OK"
            if any(
                coverage.get("beatmap_ar", {}).get(c, {}).get("count", 0) > 0
                for c in ("low", "medium", "high")
            )
            else "MISSING"
        ),
        ", ".join(
            f"{c}:{coverage.get('beatmap_ar', {}).get(c, {}).get('count', 0)}"
            for c in ("low", "medium", "high")
        ),
    )
    _add_row(
        table,
        "Beatmap CS",
        (
            "OK"
            if any(
                coverage.get("beatmap_cs", {}).get(c, {}).get("count", 0) > 0
                for c in ("low", "medium", "high")
            )
            else "MISSING"
        ),
        ", ".join(
            f"{c}:{coverage.get('beatmap_cs', {}).get(c, {}).get('count', 0)}"
            for c in ("low", "medium", "high")
        ),
    )

    cc = coverage.get("country_codes", {})
    _add_row(table, "Country Codes", "OK" if cc else "MISSING", str(len(cc)))
    restr = coverage.get("restricted_users", {})
    _add_row(
        table,
        "Restricted Users",
        (
            "OK"
            if restr.get("true", {}).get("count", 0) > 0
            and restr.get("false", {}).get("count", 0) > 0
            else "PARTIAL"
        ),
        f"true:{restr.get('true', {}).get('count', 0)}, false:{restr.get('false', {}).get('count', 0)}",
    )


def _add_row(table, category: str, status: str, details: str) -> None:
    if status == "OK":
        style = "green"
    elif status == "PARTIAL":
        style = "yellow"
    else:
        style = "red"
    table.add_row(f"[{style}]{category}[/{style}]", f"[{style}]{status}[/{style}]", details)
