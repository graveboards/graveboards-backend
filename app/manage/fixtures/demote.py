from datetime import datetime, timezone
from shutil import copy2

from rich.console import Console
from rich.prompt import Confirm

from app.fixtures.utils import TEST_FIXTURES_DIR, FIXTURES_DIR, load_metadata, save_metadata
from .helpers import get_categories_to_process

console = Console()


async def cmd_demote_fixtures(
    beatmaps: bool,
    beatmapsets: bool,
    users: bool,
    scores: bool,
    beatmap_scores: bool,
    beatmap_attributes: bool,
    force: bool = False,
):
    if not force:
        response = Confirm.ask("This will move fixture files back to instance fixtures. Continue?", default=False)
        if not response:
            console.print("[dim]Aborted.[/dim]")
            return

    moved = 0
    missing = 0
    current_time = datetime.now(timezone.utc).isoformat()

    console.print("\n[bold]=== Demoting Fixtures ===[/bold]\n")

    categories_to_demote = get_categories_to_process(
        beatmaps=beatmaps,
        beatmapsets=beatmapsets,
        users=users,
        scores=scores,
        beatmap_scores=beatmap_scores,
        beatmap_attributes=beatmap_attributes,
    )

    metadata = load_metadata()

    for category in categories_to_demote:
        src_path = TEST_FIXTURES_DIR / category
        dst_path = FIXTURES_DIR / category

        if category in ["beatmaps", "beatmapsets", "beatmap_scores", "beatmap_attributes"]:
            dst_path.mkdir(parents=True, exist_ok=True)
            if src_path.exists():
                files = list(src_path.glob("*.json"))
                count = len(files)
                for filepath in files:
                    if not filepath.exists():
                        missing += 1
                        continue
                    copy2(filepath, dst_path / filepath.name)
                    moved += 1
                    filepath.unlink(missing_ok=True)
                metadata["promoted_fixtures"][category] = metadata["promoted_fixtures"].setdefault(category, {"count": 0})
                metadata["promoted_fixtures"][category]["count"] = max(0, metadata["promoted_fixtures"][category].get("count", 0) - count)
                metadata["promoted_fixtures"][category]["last_promoted"] = current_time
                metadata["samples"][category] = metadata["samples"].setdefault(category, {"count": 0})
                metadata["samples"][category]["count"] = metadata["samples"][category].get("count", 0) + count
        elif category in ["users", "scores"]:
            dst_path.mkdir(parents=True, exist_ok=True)
            total_count = 0
            if src_path.exists():
                for sub in src_path.iterdir():
                    if sub.is_dir():
                        sub_dst = dst_path / sub.name
                        sub_dst.mkdir(parents=True, exist_ok=True)
                        files = list(sub.glob("*.json"))
                        count = len(files)
                        total_count += count
                        for filepath in files:
                            if not filepath.exists():
                                missing += 1
                                continue
                            copy2(filepath, sub_dst / filepath.name)
                            moved += 1
                            filepath.unlink(missing_ok=True)
                        if category == "users":
                            metadata["promoted_fixtures"][category] = metadata["promoted_fixtures"].setdefault(category, {"count": 0, "per_ruleset": {}})
                            metadata["promoted_fixtures"][category]["per_ruleset"] = metadata["promoted_fixtures"][category].setdefault("per_ruleset", {})
                            metadata["promoted_fixtures"][category]["per_ruleset"][sub.name] = max(0, metadata["promoted_fixtures"][category]["per_ruleset"].get(sub.name, 0) - count)
                            metadata["samples"]["users"] = metadata["samples"].setdefault("users", {"per_ruleset": {}})
                            metadata["samples"]["users"]["per_ruleset"] = metadata["samples"]["users"].setdefault("per_ruleset", {})
                            metadata["samples"]["users"]["per_ruleset"][sub.name] = metadata["samples"]["users"]["per_ruleset"].get(sub.name, 0) + count
                        else:
                            metadata["promoted_fixtures"][category] = metadata["promoted_fixtures"].setdefault(category, {"count": 0, "per_type": {}})
                            metadata["promoted_fixtures"][category]["per_type"] = metadata["promoted_fixtures"][category].setdefault("per_type", {})
                            metadata["promoted_fixtures"][category]["per_type"][sub.name] = max(0, metadata["promoted_fixtures"][category]["per_type"].get(sub.name, 0) - count)
                            metadata["samples"]["scores"] = metadata["samples"].setdefault("scores", {"per_type": {}})
                            metadata["samples"]["scores"]["per_type"] = metadata["samples"]["scores"].setdefault("per_type", {})
                            metadata["samples"]["scores"]["per_type"][sub.name] = metadata["samples"]["scores"]["per_type"].get(sub.name, 0) + count
                metadata["promoted_fixtures"][category] = metadata["promoted_fixtures"].setdefault(category, {"count": 0})
                metadata["promoted_fixtures"][category]["count"] = max(0, metadata["promoted_fixtures"][category].get("count", 0) - total_count)
                metadata["promoted_fixtures"][category]["last_promoted"] = current_time
                metadata["samples"][category] = metadata["samples"].setdefault(category, {"count": 0})
                metadata["samples"][category]["count"] = metadata["samples"][category].get("count", 0) + total_count

    save_metadata(metadata)

    if missing > 0:
        console.print(f"  [yellow]⚠️ {missing} file(s) already missing, skipped[/yellow]")
    console.print(f"[green]✅ Demoted {moved} fixture files from tests/fixtures/osu/[/green]")
