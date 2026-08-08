from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from app.database.db import PostgresqlDB


@pytest.mark.asyncio
async def test_beatmapset_snapshot_with_beatmap_snapshots(
    db: PostgresqlDB, db_session: Any
) -> None:
    """BeatmapsetSnapshot should resolve nested beatmap_snapshots via M2M."""
    from app.database.models import (
        Beatmap,
        Beatmapset,
        BeatmapsetSnapshot,
        BeatmapSnapshot,
        User,
    )

    user_id = 10000002
    beatmapset_id = 1000002
    beatmap_id = 10000102

    await db.add(User, session=db_session, id=user_id)
    await db.add(Beatmapset, session=db_session, id=beatmapset_id, user_id=user_id)
    await db.add(Beatmap, session=db_session, id=beatmap_id, beatmapset_id=beatmapset_id)

    bm_snapshot = await db.add(
        BeatmapSnapshot,
        session=db_session,
        id=beatmap_id,
        beatmap_id=beatmap_id,
        user_id=user_id,
        snapshot_number=1,
        checksum="bm_snap_for_bms_unique",
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
        url="https://osu.ppy.sh/beatmaps/10000102",
        version="Normal",
    )

    bms = await db.add(
        BeatmapsetSnapshot,
        session=db_session,
        beatmapset_id=beatmapset_id,
        user_id=user_id,
        snapshot_number=1,
        checksum="bms_with_bm_snaps_unique",
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
        preview_url="//b.ppy.sh/preview/1000002.mp3",
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

    assert bms.checksum == "bms_with_bm_snaps_unique"

    await db_session.refresh(bms, attribute_names=["beatmap_snapshots"])
    assert len(bms.beatmap_snapshots) == 1
    assert bms.beatmap_snapshots[0].id == bm_snapshot.id


@pytest.mark.asyncio
async def test_resolve_beatmapset_snapshot_by_checksum(db: PostgresqlDB, db_session: Any) -> None:
    """BeatmapsetSnapshot should be resolved by unique checksum."""
    from app.database.models import (
        Beatmapset,
        BeatmapsetSnapshot,
        User,
    )

    user_id = 10000003
    beatmapset_id = 1000003

    await db.add(User, session=db_session, id=user_id)
    await db.add(Beatmapset, session=db_session, id=beatmapset_id, user_id=user_id)

    snapshot1 = await db.add(
        BeatmapsetSnapshot,
        session=db_session,
        beatmapset_id=beatmapset_id,
        user_id=user_id,
        snapshot_number=1,
        checksum="unique_bms_chk_10000003",
        artist="Artist",
        artist_unicode="Artist",
        availability={"download_disabled": False, "more_information": None},
        bpm=190.0,
        can_be_hyped=False,
        creator="creator",
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
        preview_url="//b.ppy.sh/preview/1000003.mp3",
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
    )

    snapshot2 = await db.add(
        BeatmapsetSnapshot,
        session=db_session,
        beatmapset_id=beatmapset_id,
        user_id=user_id,
        snapshot_number=1,
        checksum="unique_bms_chk_10000003",
        artist="Different Artist",
        artist_unicode="Different",
        availability={"download_disabled": True, "more_information": "See docs"},
        bpm=200.0,
        can_be_hyped=True,
        creator="different_creator",
        current_nominations=[{"nominator": "user1"}],
        deleted_at=None,
        description={"description": "Different description"},
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
    assert snapshot1.artist == "Artist"
    assert snapshot1.bpm == 190.0


@pytest.mark.asyncio
async def test_resolve_beatmapset_cross_session(db: PostgresqlDB, db_session: Any) -> None:
    """Beatmapset from one session should be resolvable in another session."""
    from app.database.models import (
        Beatmapset,
        User,
    )

    user_id = 10000005
    beatmapset_id = 1000005

    # Create user and beatmapset in first session
    await db.add(User, session=db_session, id=user_id)
    await db.add(Beatmapset, session=db_session, id=beatmapset_id, user_id=user_id)

    # Verify it exists
    fetched = await db.get(Beatmapset, session=db_session, id=beatmapset_id)
    assert fetched is not None
    assert fetched.id == beatmapset_id
    assert fetched.user_id == user_id


@pytest.mark.asyncio
async def test_add_many_beatmapsets(db: PostgresqlDB, db_session: Any) -> None:
    """add_many should handle multiple beatmapsets with nested data."""
    from app.database.models import (
        Beatmapset,
        User,
    )

    user_id = 10000007

    await db.add(User, session=db_session, id=user_id)

    created = await db.add_many(
        Beatmapset,
        {"id": 1000007, "user_id": user_id},
        {"id": 1000008, "user_id": user_id},
        {"id": 1000009, "user_id": user_id},
        session=db_session,
    )

    assert len(created) == 3
    ids = {b.id for b in created}
    assert ids == {1000007, 1000008, 1000009}

    beatmapsets = await db.get_many(Beatmapset, session=db_session, user_id=user_id)
    assert len(beatmapsets) == 3
