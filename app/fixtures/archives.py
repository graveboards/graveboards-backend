"""Archive system for osu.sh data source.

This module provides tools to discover, index, and extract data from
the osu.sh data archives (https://data.ppy.sh/).
"""
import re
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

import httpx

from app.config import PROJECT_ROOT
from app.logging import get_logger
from app.fixtures.constants import RULESETS

logger = get_logger(__name__)

ARCHIVE_BASE_URL = "https://data.ppy.sh/"
ARCHIVE_DIR = PROJECT_ROOT / "instance" / "data_ppy_sh"
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

INDEX_FILE = ARCHIVE_DIR / "archive_index.json"
SQL_CACHE_DIR = ARCHIVE_DIR / "sql_cache"
SQL_CACHE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ArchiveInfo:
    """Information about an available archive."""
    filename: str
    url: str
    date: datetime
    archive_type: str
    ruleset: Optional[str] = None
    selection: Optional[str] = None
    count: Optional[int] = None
    compressed_size: Optional[int] = None
    uncompressed_size: Optional[int] = None


@dataclass
class ArchiveIndex:
    """Indexed archives with metadata."""
    archives: dict[str, ArchiveInfo] = field(default_factory=dict)
    last_updated: Optional[datetime] = None
    ruleset_archives: dict[str, dict[str, list[ArchiveInfo]]] = field(
        default_factory=lambda: {ruleset: {"top": [], "random": []} for ruleset in RULESETS}
    )
    
    def get_latest_archive(
        self,
        archive_type: str,
        ruleset: Optional[str] = None,
        selection: Optional[str] = None,
    ) -> Optional[ArchiveInfo]:
        """Get the latest archive matching criteria."""
        candidates = []
        
        for archive in self.archives.values():
            if archive.archive_type != archive_type:
                continue
            if ruleset and archive.ruleset != ruleset:
                continue
            if selection and archive.selection != selection:
                continue
            candidates.append(archive)
        
        if not candidates:
            return None
        
        return max(candidates, key=lambda a: a.date)


def parse_archive_filename(filename: str) -> Optional[ArchiveInfo]:
    """Parse an archive filename to extract metadata."""
    osu_files_pattern = r"^(\d{4})_(\d{2})_(\d{2})_osu_files\.tar\.bz2$"
    match = re.match(osu_files_pattern, filename)
    if match:
        year, month, day = match.groups()
        return ArchiveInfo(
            filename=filename,
            url=f"{ARCHIVE_BASE_URL}{filename}",
            date=datetime(int(year), int(month), int(day)),
            archive_type="osu_files",
        )
    
    perf_pattern = r"^(\d{4})_(\d{2})_(\d{2})_performance_(\w+)_(top|random)_(\d+)\.tar\.bz2$"
    match = re.match(perf_pattern, filename)
    if match:
        year, month, day, ruleset, selection, count = match.groups()
        if ruleset not in RULESETS:
            return None
        return ArchiveInfo(
            filename=filename,
            url=f"{ARCHIVE_BASE_URL}{filename}",
            date=datetime(int(year), int(month), int(day)),
            archive_type="performance",
            ruleset=ruleset,
            selection=selection,
            count=int(count),
        )
    
    return None


async def fetch_archive_index() -> list[str]:
    """Fetch the list of available archives from osu.sh."""
    async with httpx.AsyncClient() as client:
        response = await client.get(ARCHIVE_BASE_URL)
        response.raise_for_status()
    
    import re
    filenames = re.findall(r'href=[\'"]([^\'"]+\.tar\.bz2)[\'"]', response.text)
    return filenames


_cached_archive_index: ArchiveIndex | None = None


def load_archive_index() -> ArchiveIndex:
    """Load the cached archive index (cached in memory)."""
    global _cached_archive_index
    
    if _cached_archive_index is not None:
        return _cached_archive_index
    
    _cached_archive_index = ArchiveIndex()
    
    if not INDEX_FILE.exists():
        return _cached_archive_index
    
    import json
    try:
        with open(INDEX_FILE) as f:
            data = json.load(f)
        
        index = ArchiveIndex(
            archives={},
            last_updated=datetime.fromisoformat(data.get("last_updated"))
        )
        
        for filename, info in data.get("archives", {}).items():
            index.archives[filename] = ArchiveInfo(
                filename=info["filename"],
                url=info["url"],
                date=datetime.fromisoformat(info["date"]),
                archive_type=info["archive_type"],
                ruleset=info.get("ruleset"),
                selection=info.get("selection"),
                count=info.get("count"),
            )
        
        for archive in index.archives.values():
            if archive.archive_type == "performance" and archive.ruleset in RULESETS:
                if archive.selection in ["top", "random"]:
                    index.ruleset_archives[archive.ruleset][archive.selection].append(archive)
        
        _cached_archive_index = index
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to load archive index: {e}")
    
    return _cached_archive_index


def clear_archive_index_cache() -> None:
    """Clear the cached archive index."""
    global _cached_archive_index
    _cached_archive_index = None


def save_archive_index(index: ArchiveIndex) -> None:
    """Save the archive index to cache."""
    import json
    
    data = {
        "last_updated": index.last_updated.isoformat() if index.last_updated else None,
        "archives": {},
    }
    
    for filename, archive in index.archives.items():
        data["archives"][filename] = {
            "filename": archive.filename,
            "url": archive.url,
            "date": archive.date.isoformat(),
            "archive_type": archive.archive_type,
            "ruleset": archive.ruleset,
            "selection": archive.selection,
            "count": archive.count,
        }
    
    with open(INDEX_FILE, "w") as f:
        json.dump(data, f, indent=2)


async def refresh_archive_index() -> ArchiveIndex:
    """Refresh the archive index from osu.sh."""
    logger.info("Refreshing archive index from osu.sh...")
    
    try:
        filenames = await fetch_archive_index()
    except Exception as e:
        logger.error(f"Failed to fetch archive list: {e}")
        return load_archive_index()
    
    index = ArchiveIndex(last_updated=datetime.now())
    
    for filename in filenames:
        try:
            archive = parse_archive_filename(filename)
            if archive:
                index.archives[filename] = archive
                
                if archive.archive_type == "performance" and archive.ruleset in RULESETS:
                    if archive.selection in ["top", "random"]:
                        index.ruleset_archives[archive.ruleset][archive.selection].append(archive)
        except Exception as e:
            logger.warning(f"Failed to parse archive filename '{filename}': {e}")
    
    save_archive_index(index)
    logger.info(f"Indexed {len(index.archives)} archives")
    
    return index


async def download_archive(archive_info: ArchiveInfo) -> Optional[Path]:
    """Download an archive from osu.sh."""
    archive_path = ARCHIVE_DIR / archive_info.filename
    
    if archive_path.exists():
        logger.info(f"Archive already exists: {archive_path}")
        return archive_path
    
    logger.info(f"Downloading {archive_info.filename}...")
    
    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("GET", archive_info.url) as response:
                response.raise_for_status()
                with open(archive_path, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
        
        logger.info(f"Downloaded {archive_info.filename} ({archive_path.stat().st_size / 1024 / 1024:.1f} MB)")
        return archive_path
    except Exception as e:
        logger.warning(f"Archive unavailable at {archive_info.url}: {e}")
        if archive_path.exists():
            archive_path.unlink()
        return None


def cleanup_archives() -> int:
    """Delete tar.bz2 files for archives that have been extracted.
    
    Returns the number of files deleted.
    """
    deleted = 0
    
    for archive_path in ARCHIVE_DIR.glob("*.tar.bz2"):
        extraction_name = archive_path.name.replace(".tar.bz2", "")
        extraction_dir = SQL_CACHE_DIR / extraction_name
        
        if extraction_dir.exists():
            archive_path.unlink()
            logger.info(f"Deleted archive (extraction exists): {archive_path}")
            deleted += 1
    
    return deleted


async def extract_sql_from_archive(archive_info: ArchiveInfo, allow_download: bool = False) -> Optional[Path]:
    """Extract SQL files from a performance archive.
    
    Args:
        archive_info: Archive metadata
        allow_download: If True, download missing archives. If False, only use cached/local files.
    """
    extraction_dir = SQL_CACHE_DIR / archive_info.filename.replace(".tar.bz2", "")
    
    if extraction_dir.exists():
        logger.info(f"Using cached extraction: {extraction_dir}")
        return extraction_dir
    
    archive_path = ARCHIVE_DIR / archive_info.filename
    
    if not archive_path.exists():
        if allow_download:
            logger.info(f"Archive not cached locally, downloading...")
            archive_path = await download_archive(archive_info)
            if not archive_path:
                return None
        else:
            return None
    
    extraction_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        import tarfile
        with tarfile.open(archive_path, "r:bz2") as tar:
            sql_members = [m for m in tar.getmembers() if m.name.endswith(".sql")]
            tar.extractall(extraction_dir, members=sql_members)
        
        logger.info(f"Extracted SQL from {archive_info.filename} to {extraction_dir}")
        
        if archive_path.exists():
            archive_path.unlink()
            logger.info(f"Deleted archive after extraction: {archive_path}")
        
        return extraction_dir
    except Exception as e:
        logger.error(f"Failed to extract {archive_path}: {e}")
        return None


def parse_performance_sql(sql_path: Path) -> dict[str, list[dict]]:
    """Parse SQL files to extract data."""
    data = {}
    
    try:
        tables = {}
        current_table = None
        current_rows = []
        
        with open(sql_path) as f:
            for line in f:
                table_match = re.match(r"CREATE TABLE `(\w+)`", line)
                if table_match:
                    if current_table and current_rows:
                        tables[current_table] = current_rows
                    current_table = table_match.group(1)
                    current_rows = []
                    continue
                
                insert_match = re.match(r"INSERT INTO `(\w+)` VALUES \((.+)\);", line)
                if insert_match:
                    table_name = insert_match.group(1)
                    values = insert_match.group(2)
                    
                    tuple_strs = values.split("),(")
                    for i, tuple_str in enumerate(tuple_strs):
                        if i == 0:
                            tuple_str = tuple_str.lstrip("(")
                        if i == len(tuple_strs) - 1:
                            tuple_str = tuple_str.rstrip(")")
                        row = parse_sql_values(tuple_str)
                        
                        if table_name not in tables:
                            tables[table_name] = []
                        tables[table_name].append(row)
        
        if current_table and current_rows:
            tables[current_table] = current_rows
        
        data = tables
    except Exception as e:
        logger.warning(f"Failed to parse SQL {sql_path}: {e}")
    
    return data


def parse_sql_values(values: str) -> list:
    """Parse SQL VALUES clause into Python values."""
    parsed = []
    current = ""
    in_string = False
    
    for char in values:
        if char == "'" and not in_string:
            in_string = True
            current = ""
        elif char == "'" and in_string:
            parsed.append(current)
            current = ""
            in_string = False
        elif char == "," and not in_string:
            if current.strip().upper() == "NULL":
                parsed.append(None)
            elif current.strip().isdigit():
                parsed.append(int(current.strip()))
            else:
                parsed.append(current.strip() if current.strip() else None)
            current = ""
        elif char == " " and not in_string:
            continue
        else:
            current += char
    
    if current:
        if current.strip().upper() == "NULL":
            parsed.append(None)
        elif current.strip().isdigit():
            parsed.append(int(current.strip()))
        else:
            parsed.append(current.strip() if current.strip() else None)
    
    return parsed


async def get_user_ids_from_archive(archive_info: ArchiveInfo, min_playcount: int = 100, allow_download: bool = False) -> list[int]:
    """Extract player IDs from a performance archive."""
    extraction_dir = await extract_sql_from_archive(archive_info, allow_download=allow_download)
    if not extraction_dir:
        return []
    
    user_ids = set()
    
    for sql_file in extraction_dir.glob("osu_user_stats*.sql"):
        try:
            data = parse_performance_sql(sql_file)
            
            for table_name, rows in data.items():
                if "user_stats" in table_name.lower():
                    for row in rows:
                        if len(row) >= 9:
                            user_id = row[0]
                            playcount = row[8]
                            
                            if user_id and playcount and playcount >= min_playcount:
                                user_ids.add(user_id)
        except Exception as e:
            logger.warning(f"Failed to parse {sql_file.name}: {e}")
    
    for sql_file in extraction_dir.glob("osu_beatmaps.sql"):
        try:
            data = parse_performance_sql(sql_file)
            for table_name, rows in data.items():
                if "beatmaps" in table_name.lower():
                    for row in rows:
                        if len(row) >= 3:
                            user_id = row[2]
                            if user_id:
                                user_ids.add(user_id)
        except Exception as e:
            logger.warning(f"Failed to parse {sql_file.name}: {e}")
    
    logger.info(f"Extracted {len(user_ids)} user IDs from {archive_info.filename}")
    return sorted(user_ids)


async def get_beatmap_ids_from_archive(archive_info: ArchiveInfo, allow_download: bool = False) -> list[int]:
    """Extract beatmap IDs from an osu_files archive."""
    extraction_dir = await extract_sql_from_archive(archive_info, allow_download=allow_download)
    if not extraction_dir:
        return []
    
    beatmap_ids = set()
    
    sql_dir = extraction_dir.parent / f"{archive_info.filename.replace('.tar.bz2', '')}_sql"
    if sql_dir.exists():
        for sql_file in sql_dir.glob("osu_beatmaps.sql"):
            try:
                data = parse_performance_sql(sql_file)
                for table_name, rows in data.items():
                    if "beatmaps" in table_name.lower():
                        for row in rows:
                            if row and isinstance(row, list) and len(row) >= 1:
                                beatmap_id = row[0]
                                if beatmap_id:
                                    beatmap_ids.add(beatmap_id)
            except Exception as e:
                logger.warning(f"Failed to parse {sql_file.name}: {e}")
    
    osu_dir = extraction_dir.parent / f"{archive_info.filename.replace('.tar.bz2', '')}_osu"
    if not osu_dir.exists() and extraction_dir.exists():
        for item in extraction_dir.iterdir():
            if item.is_dir() and not item.name.endswith(".sql"):
                osu_dir = item
                break
    
    if osu_dir and osu_dir.exists():
        for osu_file in osu_dir.glob("*.osu"):
            try:
                with open(osu_file) as f:
                    for line in f:
                        if line.startswith("BeatmapID:"):
                            beatmap_id = int(line.split(":")[1].strip())
                            beatmap_ids.add(beatmap_id)
                            break
            except (ValueError, IOError):
                continue
    
    logger.info(f"Extracted {len(beatmap_ids)} beatmap IDs from {archive_info.filename}")
    return sorted(beatmap_ids)
