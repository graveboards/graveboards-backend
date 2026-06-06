from datetime import datetime, timezone
from shutil import copy2, rmtree

from rich.console import Console

from app.fixtures.utils import FIXTURES_DIR, TEST_FIXTURES_DIR, load_metadata, save_metadata, create_empty_samples
from app.logging import get_logger
from .helpers import get_categories_to_process

console = Console()
logger = get_logger(__name__)


async def cmd_promote_fixtures(
    beatmaps: bool,
    beatmapsets: bool,
    users: bool,
    scores: bool,
    beatmap_scores: bool,
    beatmap_attributes: bool,
):
    metadata = load_metadata()
    copied = 0
    current_time = datetime.now(timezone.utc).isoformat()

    console.print("\n[bold]=== Promoting Fixtures ===[/bold]\n")

    categories_to_promote = get_categories_to_process(
        beatmaps=beatmaps,
        beatmapsets=beatmapsets,
        users=users,
        scores=scores,
        beatmap_scores=beatmap_scores,
        beatmap_attributes=beatmap_attributes,
    )

    for src_name, dst_name, meta_name in categories_to_promote:
        src_path = FIXTURES_DIR / src_name
        dst_path = TEST_FIXTURES_DIR / dst_name

        if src_name in ["beatmaps", "beatmapsets", "beatmap_scores", "beatmap_attributes"]:
            dst_path.mkdir(parents=True, exist_ok=True)
            if src_path.exists():
                count = len(list(src_path.glob("*.json")))
                for filepath in src_path.glob("*.json"):
                    copy2(filepath, dst_path / filepath.name)
                    copied += 1
                rmtree(src_path)
                metadata["promoted_fixtures"][meta_name] = {
                    "count": metadata["promoted_fixtures"][meta_name].get("count", 0) + count,
                    "last_promoted": current_time,
                }
        elif src_name in ["users", "scores"]:
            dst_path.mkdir(parents=True, exist_ok=True)
            total_count = 0
            if src_path.exists():
                for sub in src_path.iterdir():
                    if sub.is_dir():
                        sub_dst = dst_path / sub.name
                        sub_dst.mkdir(parents=True, exist_ok=True)
                        count = len(list(sub.glob("*.json")))
                        total_count += count
                        for filepath in sub.glob("*.json"):
                            copy2(filepath, sub_dst / filepath.name)
                            copied += 1
                        rmtree(sub)
                        if src_name == "users":
                            if meta_name not in metadata["promoted_fixtures"]:
                                metadata["promoted_fixtures"][meta_name] = {"count": 0, "per_ruleset": {}}
                            if "per_ruleset" not in metadata["promoted_fixtures"][meta_name]:
                                metadata["promoted_fixtures"][meta_name]["per_ruleset"] = {}
                            metadata["promoted_fixtures"][meta_name]["per_ruleset"][sub.name] = metadata["promoted_fixtures"][meta_name]["per_ruleset"].get(sub.name, 0) + count
                        else:
                            if meta_name not in metadata["promoted_fixtures"]:
                                metadata["promoted_fixtures"][meta_name] = {"count": 0, "per_type": {}}
                            if "per_type" not in metadata["promoted_fixtures"][meta_name]:
                                metadata["promoted_fixtures"][meta_name]["per_type"] = {}
                            metadata["promoted_fixtures"][meta_name]["per_type"][sub.name] = metadata["promoted_fixtures"][meta_name]["per_type"].get(sub.name, 0) + count
                src_path.rmdir()
                metadata["promoted_fixtures"][meta_name]["count"] = metadata["promoted_fixtures"][meta_name].get("count", 0) + total_count
                metadata["promoted_fixtures"][meta_name]["last_promoted"] = current_time

    if metadata.get("last_updated"):
        metadata["last_updated"] = None
        metadata["samples"] = create_empty_samples()
    save_metadata(metadata)

    console.print(f"[green]✅ Promoted {copied} fixture files to tests/fixtures/osu/[/green]")
    console.print("   [dim]Instance fixtures cleaned up[/dim]\n")
