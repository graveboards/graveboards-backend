from datetime import datetime

import pytest

from app.database.models import Beatmap, Beatmapset, BeatmapSnapshot, BeatmapsetSnapshot
from tests.fixtures.osu import load_beatmap, load_beatmapset


async def seed_beatmapset(
    session,
    beatmapset_id: int,
    beatmap_ids: list[int],
    user_id: int = 12345,
) -> tuple[Beatmapset, list[Beatmap], BeatmapsetSnapshot, list[BeatmapSnapshot]]:
    """Seed a beatmapset and its beatmaps into the database."""
    beatmapset_data = load_beatmapset(f"beatmapset_{beatmapset_id}")
    beatmaps = []
    beatmap_snapshots = []

    beatmapset = Beatmapset(id=beatmapset_id, user_id=user_id)
    session.add(beatmapset)
    await session.flush()

    for beatmap_id in beatmap_ids:
        beatmap_data = load_beatmap(f"beatmap_{beatmap_id}")
        beatmap = Beatmap(
            id=beatmap_id,
            beatmapset_id=beatmapset_id,
        )
        session.add(beatmap)
        await session.flush()

        beatmaps.append(beatmap)

        beatmap_snapshot = BeatmapSnapshot(
            beatmap_id=beatmap_id,
            user_id=user_id,
            snapshot_number=1,
            accuracy=beatmap_data.get("accuracy", 100.0),
            ar=beatmap_data.get("ar", 9.0),
            beatmapset_id=beatmapset_id,
            bpm=beatmap_data.get("bpm", 120.0),
            checksum=beatmap_data.get("checksum", "dummy_checksum"),
            count_circles=beatmap_data.get("count_circles", 100),
            count_sliders=beatmap_data.get("count_sliders", 50),
            count_spinners=beatmap_data.get("count_spinners", 10),
            cs=beatmap_data.get("cs", 4.0),
            difficulty_rating=beatmap_data.get("difficulty_rating", 5.0),
            drain=beatmap_data.get("drain", 5.0),
            failtimes=beatmap_data.get("failtimes", {}),
            hit_length=beatmap_data.get("hit_length", 180),
            is_scoreable=beatmap_data.get("is_scoreable", True),
            last_updated=datetime.fromisoformat(beatmap_data.get("last_updated", "2024-01-01T00:00:00+00:00").replace("Z", "+00:00")),
            max_combo=beatmap_data.get("max_combo", 1000),
            mode=beatmap_data.get("mode", "osu"),
            mode_int=beatmap_data.get("mode_int", 0),
            passcount=beatmap_data.get("passcount", 100),
            playcount=beatmap_data.get("playcount", 1000),
            ranked=beatmap_data.get("ranked", 1),
            status=beatmap_data.get("status", "ranked"),
            total_length=beatmap_data.get("total_length", 200),
            url=beatmap_data.get("url", "https://osu.ppy.sh/b/12345"),
            version=beatmap_data.get("version", "Hard"),
        )
        session.add(beatmap_snapshot)
        await session.flush()

        beatmap_snapshots.append(beatmap_snapshot)

    beatmapset_snapshot = BeatmapsetSnapshot(
        beatmapset_id=beatmapset_id,
        user_id=user_id,
        snapshot_number=1,
        checksum=f"dummy_checksum_{beatmapset_id}",
        artist=beatmapset_data.get("artist", "Test Artist"),
        artist_unicode=beatmapset_data.get("artist_unicode", "Test Artist"),
        availability=beatmapset_data.get("availability", {"download_disabled": False, "more_information": None}),
        bpm=beatmapset_data.get("bpm", 120.0),
        can_be_hyped=beatmapset_data.get("can_be_hyped", True),
        covers=beatmapset_data.get("covers", {"cover": "https://example.com/cover.jpg", "cover@2x": "https://example.com/cover@2x.jpg"}),
        creator=beatmapset_data.get("creator", "testuser"),
        current_nominations=beatmapset_data.get("current_nominations", {"nominators": [], "required": 2}),
        description=beatmapset_data.get("description", {"description": ""}),
        discussion_enabled=beatmapset_data.get("discussion_enabled", True),
        discussion_locked=beatmapset_data.get("discussion_locked", False),
        favourite_count=beatmapset_data.get("favourite_count", 0),
        genre=beatmapset_data.get("genre", {"id": 1, "name": "Any"}),
        hype=beatmapset_data.get("hype", None),
        is_scoreable=beatmapset_data.get("is_scoreable", True),
        language=beatmapset_data.get("language", {"id": 1, "name": "Any"}),
        last_updated=datetime.fromisoformat(beatmapset_data.get("last_updated", "2024-01-01T00:00:00+00:00").replace("Z", "+00:00")),
        legacy_thread_url=beatmapset_data.get("legacy_thread_url", None),
        nominations_summary=beatmapset_data.get("nominations_summary", {"current": 2, "required": 2, "required_meta": {"main_ruleset": 2, "non_main_ruleset": 1}}),
        nsfw=beatmapset_data.get("nsfw", False),
        offset=beatmapset_data.get("offset", 0),
        pack_tags=beatmapset_data.get("pack_tags", []),
        play_count=beatmapset_data.get("play_count", 0),
        preview_url=beatmapset_data.get("preview_url", "https://example.com/preview.mp3"),
        ranked=beatmapset_data.get("ranked", 1),
        ranked_date=datetime.fromisoformat(beatmapset_data.get("ranked_date", "2024-01-01T00:00:00+00:00").replace("Z", "+00:00")) if beatmapset_data.get("ranked_date") else None,
        rating=beatmapset_data.get("rating", 5.0),
        ratings=beatmapset_data.get("ratings", [5]),
        source=beatmapset_data.get("source", ""),
        spotlight=beatmapset_data.get("spotlight", False),
        status=beatmapset_data.get("status", "ranked"),
        storyboard=beatmapset_data.get("storyboard", False),
        submitted_date=datetime.fromisoformat(beatmapset_data.get("submitted_date", "2024-01-01T00:00:00+00:00").replace("Z", "+00:00")) if beatmapset_data.get("submitted_date") else None,
        tags=beatmapset_data.get("tags", "test tags"),
        title=beatmapset_data.get("title", "Test Song"),
        title_unicode=beatmapset_data.get("title_unicode", "Test Song"),
        track_id=beatmapset_data.get("track_id", None),
        video=beatmapset_data.get("video", False),
    )
    session.add(beatmapset_snapshot)
    await session.flush()

    for beatmap_snapshot in beatmap_snapshots:
        beatmapset_snapshot.beatmap_snapshots.append(beatmap_snapshot)

    return beatmapset, beatmaps, beatmapset_snapshot, beatmap_snapshots


@pytest.fixture
async def seeded_beatmapsets(db_transaction):
    """Fixture to seed multiple beatmapsets for testing."""
    beatmapsets = []
    for beatmapset_id in [35965, 54321]:
        beatmapset, _, _, _ = await seed_beatmapset(
            db_transaction,
            beatmapset_id=beatmapset_id,
            beatmap_ids=[beatmapset_id * 10 + 1, beatmapset_id * 10 + 2],
        )
        beatmapsets.append(beatmapset)
    await db_transaction.commit()
    return beatmapsets


@pytest.fixture
async def seeded_beatmaps(db_transaction):
    """Fixture to seed multiple beatmaps for testing."""
    beatmaps = []
    beatmap_ids = [116383, 234567, 345678]
    for i, beatmap_id in enumerate(beatmap_ids):
        beatmapset_id = beatmap_id
        beatmapset, beatmaps_list, _, _ = await seed_beatmapset(
            db_transaction,
            beatmapset_id=beatmapset_id,
            beatmap_ids=[beatmap_id],
            user_id=12345 + i,
        )
        beatmaps.extend(beatmaps_list)
    await db_transaction.commit()
    return beatmaps
