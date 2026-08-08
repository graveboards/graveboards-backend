from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from app.database.db import PostgresqlDB


@pytest.mark.asyncio
async def test_add_many_beatmap_snapshots(db: PostgresqlDB, db_session: Any) -> None:
    """add_many should handle multiple BeatmapSnapshots."""
    from app.database.models import (
        Beatmap,
        Beatmapset,
        BeatmapSnapshot,
        User,
    )

    user_id = 10000017
    beatmapset_id = 1000017
    beatmap_id = 10000117

    await db.add(User, session=db_session, id=user_id)
    await db.add(Beatmapset, session=db_session, id=beatmapset_id, user_id=user_id)
    await db.add(Beatmap, session=db_session, id=beatmap_id, beatmapset_id=beatmapset_id)

    created = await db.add_many(
        BeatmapSnapshot,
        {
            "id": 10000217,
            "beatmap_id": beatmap_id,
            "user_id": user_id,
            "snapshot_number": 1,
            "checksum": "am_bmsnap_u17a",
            "accuracy": 4.0,
            "ar": 5.0,
            "beatmapset_id": beatmapset_id,
            "bpm": 190.0,
            "count_circles": 92,
            "count_sliders": 206,
            "count_spinners": 2,
            "cs": 3.0,
            "difficulty_rating": 2.24,
            "drain": 4.0,
            "failtimes": {"exit": [], "fail": []},
            "hit_length": 223,
            "is_scoreable": False,
            "last_updated": "2017-07-27T22:54:47+00:00",
            "max_combo": 707,
            "mode": "osu",
            "mode_int": 0,
            "passcount": 0,
            "playcount": 1,
            "ranked": -2,
            "status": "graveyard",
            "total_length": 241,
            "url": "https://osu.ppy.sh/beatmaps/10000117",
            "version": "Normal",
        },
        {
            "id": 10000218,
            "beatmap_id": beatmap_id,
            "user_id": user_id,
            "snapshot_number": 2,
            "checksum": "am_bmsnap_u17b",
            "accuracy": 4.5,
            "ar": 5.5,
            "beatmapset_id": beatmapset_id,
            "bpm": 190.0,
            "count_circles": 95,
            "count_sliders": 210,
            "count_spinners": 2,
            "cs": 3.2,
            "difficulty_rating": 2.5,
            "drain": 4.2,
            "failtimes": {"exit": [], "fail": []},
            "hit_length": 225,
            "is_scoreable": False,
            "last_updated": "2018-01-01T00:00:00+00:00",
            "max_combo": 720,
            "mode": "osu",
            "mode_int": 0,
            "passcount": 5,
            "playcount": 20,
            "ranked": -2,
            "status": "graveyard",
            "total_length": 241,
            "url": "https://osu.ppy.sh/beatmaps/10000117",
            "version": "Hard",
        },
        session=db_session,
    )

    assert len(created) == 2
    checksums = {s.checksum for s in created}
    assert checksums == {"am_bmsnap_u17a", "am_bmsnap_u17b"}

    snapshot_numbers = {s.snapshot_number for s in created}
    assert snapshot_numbers == {1, 2}


@pytest.mark.asyncio
async def test_resolve_existing_bmsnap_via_bms_creation(db: PostgresqlDB, db_session: Any) -> None:
    """When creating a BeatmapsetSnapshot with nested BeatmapSnapshot dicts, existing BeatmapSnapshots should be resolved not re-created."""
    from app.database.models import (
        Beatmap,
        Beatmapset,
        BeatmapsetSnapshot,
        BeatmapSnapshot,
        User,
    )

    user_id = 10000018
    beatmapset_id = 1000018
    beatmap_id = 10000118

    await db.add(User, session=db_session, id=user_id)
    await db.add(Beatmapset, session=db_session, id=beatmapset_id, user_id=user_id)
    await db.add(Beatmap, session=db_session, id=beatmap_id, beatmapset_id=beatmapset_id)

    existing_count = await db.get_many(BeatmapSnapshot, session=db_session, beatmap_id=beatmap_id)
    initial_count = len(existing_count)

    bm_snapshot = await db.add(
        BeatmapSnapshot,
        session=db_session,
        id=beatmap_id,
        beatmap_id=beatmap_id,
        user_id=user_id,
        snapshot_number=1,
        checksum="resolve_existing_bmsnap_unique",
        accuracy=4.0,
        ar=5.0,
        beatmapset_id=beatmapset_id,
        bpm=190.0,
        count_circles=92,
        count_sliders=206,
        count_spinners=2,
        cs=3.0,
        difficulty_rating=2.24,
        drain=4.0,
        failtimes={"exit": [], "fail": []},
        hit_length=223,
        is_scoreable=False,
        last_updated="2017-07-27T22:54:47+00:00",
        max_combo=707,
        mode="osu",
        mode_int=0,
        passcount=0,
        playcount=1,
        ranked=-2,
        status="graveyard",
        total_length=241,
        url="https://osu.ppy.sh/beatmaps/10000118",
        version="Normal",
    )

    bms = await db.add(
        BeatmapsetSnapshot,
        session=db_session,
        beatmapset_id=beatmapset_id,
        user_id=user_id,
        snapshot_number=1,
        checksum="resolve_existing_bms_unique",
        artist="Test Artist",
        artist_unicode="Test Artist",
        availability={"download_disabled": False, "more_information": None},
        bpm=190.0,
        can_be_hyped=False,
        creator="testmapper",
        current_nominations=[],
        deleted_at=None,
        description={"description": "Test"},
        discussion_enabled=True,
        discussion_locked=False,
        favourite_count=0,
        is_scoreable=False,
        last_updated="2017-07-27T22:54:47+00:00",
        nominations_summary={
            "current": 0,
            "eligible_main_rulesets": ["osu"],
            "required_meta": {"main_ruleset": 2, "non_main_ruleset": 1},
        },
        nsfw=False,
        offset=0,
        pack_tags=[],
        play_count=0,
        preview_url="//b.ppy.sh/preview/1000018.mp3",
        ranked=-2,
        rating=0,
        ratings=[0] * 10,
        source="Test",
        spotlight=False,
        status="graveyard",
        storyboard=False,
        submitted_date="2017-06-07T03:50:21+00:00",
        tags="test",
        title="Test Song",
        title_unicode="Test Song",
        track_id=None,
        video=False,
        beatmap_snapshots=[
            {"id": bm_snapshot.id},
        ],
    )

    assert bms.checksum == "resolve_existing_bms_unique"

    final_count = await db.get_many(BeatmapSnapshot, session=db_session, beatmap_id=beatmap_id)
    assert len(final_count) == initial_count + 1

    await db_session.refresh(bms, attribute_names=["beatmap_snapshots"])
    assert len(bms.beatmap_snapshots) == 1
    assert bms.beatmap_snapshots[0].id == bm_snapshot.id
    assert bms.beatmap_snapshots[0].checksum == "resolve_existing_bmsnap_unique"
