from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from app.database.db import PostgresqlDB


@pytest.mark.asyncio
async def test_add_many_beatmapset_snapshots(db: PostgresqlDB, db_session: Any) -> None:
    """add_many should handle multiple beatmapset snapshots with nested beatmap snapshots."""
    from app.database.models import (
        Beatmap,
        Beatmapset,
        BeatmapsetSnapshot,
        BeatmapSnapshot,
        User,
    )

    user_id = 10000008
    beatmapset_id = 1000008
    beatmap_id = 10000108

    await db.add(User, session=db_session, id=user_id)
    await db.add(Beatmapset, session=db_session, id=beatmapset_id, user_id=user_id)
    await db.add(Beatmap, session=db_session, id=beatmap_id, beatmapset_id=beatmapset_id)

    bm1 = await db.add(
        BeatmapSnapshot,
        session=db_session,
        id=10000108,
        beatmap_id=beatmap_id,
        user_id=user_id,
        snapshot_number=1,
        checksum="add_many_bm_unique_10000008",
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
        url="https://osu.ppy.sh/beatmaps/10000108",
        version="Normal",
    )

    created = await db.add_many(
        BeatmapsetSnapshot,
        {
            "beatmapset_id": beatmapset_id,
            "user_id": user_id,
            "snapshot_number": 30,
            "checksum": "add_many_bms_unique_10000008_1",
            "artist": "Artist 1",
            "artist_unicode": "Artist 1",
            "availability": {"download_disabled": False, "more_information": None},
            "bpm": 190.0,
            "can_be_hyped": False,
            "creator": "creator",
            "current_nominations": [],
            "deleted_at": None,
            "description": {"description": "Test 1"},
            "discussion_enabled": True,
            "discussion_locked": False,
            "favourite_count": 0,
            "is_scoreable": False,
            "last_updated": "2017-07-27T22:54:47+00:00",
            "nominations_summary": {
                "current": 0,
                "eligible_main_rulesets": ["osu"],
                "required_meta": {"main_ruleset": 2, "non_main_ruleset": 1},
            },
            "nsfw": False,
            "offset": 0,
            "pack_tags": [],
            "play_count": 0,
            "preview_url": "//b.ppy.sh/preview/1000008.mp3",
            "ranked": -2,
            "rating": 0,
            "ratings": [0] * 10,
            "source": "Test",
            "spotlight": False,
            "status": "graveyard",
            "storyboard": False,
            "submitted_date": "2017-06-07T03:50:21+00:00",
            "tags": "test1_unique",
            "title": "Test Song 1 Unique",
            "title_unicode": "Test Song 1 Unique",
            "track_id": None,
            "video": False,
            "beatmap_snapshots": [{"id": bm1.id}],
        },
        {
            "beatmapset_id": beatmapset_id,
            "user_id": user_id,
            "snapshot_number": 31,
            "checksum": "add_many_bms_unique_10000008_2",
            "artist": "Artist 2",
            "artist_unicode": "Artist 2",
            "availability": {"download_disabled": False, "more_information": None},
            "bpm": 200.0,
            "can_be_hyped": True,
            "creator": "creator",
            "current_nominations": [],
            "deleted_at": None,
            "description": {"description": "Test 2"},
            "discussion_enabled": True,
            "discussion_locked": False,
            "favourite_count": 0,
            "is_scoreable": False,
            "last_updated": "2018-01-01T00:00:00+00:00",
            "nominations_summary": {
                "current": 0,
                "eligible_main_rulesets": ["osu"],
                "required_meta": {"main_ruleset": 2, "non_main_ruleset": 1},
            },
            "nsfw": False,
            "offset": 0,
            "pack_tags": [],
            "play_count": 0,
            "preview_url": "//b.ppy.sh/preview/1000008.mp3",
            "ranked": -2,
            "rating": 0,
            "ratings": [0] * 10,
            "source": "Test",
            "spotlight": False,
            "status": "graveyard",
            "storyboard": False,
            "submitted_date": "2018-01-01T00:00:00+00:00",
            "tags": "test2_unique",
            "title": "Test Song 2 Unique",
            "title_unicode": "Test Song 2 Unique",
            "track_id": None,
            "video": False,
            "beatmap_snapshots": [{"id": bm1.id}],
        },
        session=db_session,
    )

    assert len(created) == 2
    checksums = {s.checksum for s in created}
    assert checksums == {"add_many_bms_unique_10000008_1", "add_many_bms_unique_10000008_2"}

    snapshots = await db.get_many(
        BeatmapsetSnapshot, session=db_session, beatmapset_id=beatmapset_id
    )
    assert len(snapshots) == 2


@pytest.mark.asyncio
async def test_resolve_bms_by_composite_unique_constraint(
    db: PostgresqlDB, db_session: Any
) -> None:
    """BeatmapsetSnapshot should be resolved by composite unique constraint (beatmapset_id, snapshot_number)."""
    from app.database.models import (
        Beatmapset,
        BeatmapsetSnapshot,
        User,
    )

    user_id = 10000009
    beatmapset_id = 1000009

    await db.add(User, session=db_session, id=user_id)
    await db.add(Beatmapset, session=db_session, id=beatmapset_id, user_id=user_id)

    snapshot1 = await db.add(
        BeatmapsetSnapshot,
        session=db_session,
        beatmapset_id=beatmapset_id,
        user_id=user_id,
        snapshot_number=5,
        checksum="comp_bms_unique_10000009_a",
        artist="Artist A",
        artist_unicode="Artist A",
        availability={"download_disabled": False, "more_information": None},
        bpm=190.0,
        can_be_hyped=False,
        creator="creator",
        current_nominations=[],
        deleted_at=None,
        description={"description": "Version A"},
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
        preview_url="//b.ppy.sh/preview/1000009.mp3",
        ranked=-2,
        rating=0,
        ratings=[0] * 10,
        source="Test",
        spotlight=False,
        status="graveyard",
        storyboard=False,
        submitted_date="2017-06-07T03:50:21+00:00",
        tags="test_comp",
        title="Test Song Comp A",
        title_unicode="Test Song Comp A",
        track_id=None,
        video=False,
    )

    snapshot2 = await db.add(
        BeatmapsetSnapshot,
        session=db_session,
        beatmapset_id=beatmapset_id,
        user_id=user_id,
        snapshot_number=5,
        checksum="comp_bms_unique_10000009_b",
        artist="Artist B",
        artist_unicode="Artist B",
        availability={"download_disabled": True, "more_information": "See docs"},
        bpm=200.0,
        can_be_hyped=True,
        creator="different_creator",
        current_nominations=[{"nominator": "user1"}],
        deleted_at=None,
        description={"description": "Version B"},
        discussion_enabled=False,
        discussion_locked=True,
        favourite_count=100,
        is_scoreable=True,
        last_updated="2018-01-01T00:00:00+00:00",
        nominations_summary={
            "current": 5,
            "eligible_main_rulesets": ["osu", "fds"],
            "required_meta": {"main_ruleset": 3, "non_main_ruleset": 2},
        },
        nsfw=True,
        offset=10,
        pack_tags=["tag1", "tag2"],
        play_count=1000,
        preview_url="//b.ppy.sh/preview/different.mp3",
        ranked=1,
        rating=5.0,
        ratings=[5] * 10,
        source="Different Source",
        spotlight=True,
        status="ranked",
        storyboard=True,
        submitted_date="2018-01-01T00:00:00+00:00",
        tags="different tags",
        title="Different Title",
        title_unicode="Different Title Unicode",
        track_id=12345,
        video=True,
    )

    assert snapshot1 is snapshot2
    assert snapshot1.artist == "Artist A"
    assert snapshot1.bpm == 190.0


@pytest.mark.asyncio
async def test_resolve_bmsnap_by_composite_unique_constraint(
    db: PostgresqlDB, db_session: Any
) -> None:
    """BeatmapSnapshot should be resolved by composite unique constraint (beatmap_id, snapshot_number)."""
    from app.database.models import (
        Beatmap,
        Beatmapset,
        BeatmapSnapshot,
        User,
    )

    user_id = 10000010
    beatmapset_id = 1000010
    beatmap_id = 10000110

    await db.add(User, session=db_session, id=user_id)
    await db.add(Beatmapset, session=db_session, id=beatmapset_id, user_id=user_id)
    await db.add(Beatmap, session=db_session, id=beatmap_id, beatmapset_id=beatmapset_id)

    snapshot1 = await db.add(
        BeatmapSnapshot,
        session=db_session,
        id=beatmap_id,
        beatmap_id=beatmap_id,
        user_id=user_id,
        snapshot_number=7,
        checksum="comp_bm_snap_unique_10000010_a",
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
        url="https://osu.ppy.sh/beatmaps/10000110",
        version="Normal",
    )

    snapshot2 = await db.add(
        BeatmapSnapshot,
        session=db_session,
        id=beatmap_id,
        beatmap_id=beatmap_id,
        user_id=user_id,
        snapshot_number=7,
        checksum="comp_bm_snap_unique_10000010_b",
        accuracy=5.0,
        ar=6.0,
        beatmapset_id=beatmapset_id,
        bpm=200.0,
        count_circles=100,
        count_sliders=200,
        count_spinners=3,
        cs=4.0,
        difficulty_rating=3.0,
        drain=5.0,
        failtimes={"exit": [1, 2, 3], "fail": [4, 5, 6]},
        hit_length=250,
        is_scoreable=True,
        last_updated="2018-01-01T00:00:00+00:00",
        max_combo=800,
        mode="mania",
        mode_int=2,
        passcount=100,
        playcount=500,
        ranked=1,
        status="ranked",
        total_length=260,
        url="https://osu.ppy.sh/beatmaps/10000110_different",
        version="Insane",
    )

    assert snapshot1 is snapshot2
    assert snapshot1.accuracy == 4.0
    assert snapshot1.bpm == 190.0
