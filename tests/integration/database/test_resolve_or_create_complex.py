"""
Comprehensive tests for _resolve_or_create with complex beatmap/beatmapset/snapshot relationships.

These tests exercise the full cascade of nested relationships:
- User -> Beatmapset (FK)
- Beatmapset -> Beatmap (1:N)
- Beatmapset -> BeatmapsetSnapshot (1:N)
- Beatmap -> BeatmapSnapshot (1:N)
- BeatmapSnapshot <-> BeatmapsetSnapshot (M2M via association table)
- BeatmapsetSnapshot -> Profile (via user_id)
- BeatmapSnapshot -> BeatmapTag (M2M)
- BeatmapSnapshot -> Profile (M2M via owner_profiles)
"""

import pytest

from app.database.db import PostgresqlDB
from app.database.models import (
    User, Profile, Beatmap, Beatmapset, BeatmapSnapshot, BeatmapsetSnapshot,
    BeatmapTag, BeatmapsetTag,
)


@pytest.fixture
def db():
    return PostgresqlDB()


@pytest.mark.asyncio
async def test_beatmap_snapshot_with_tags_and_owners(db, db_session):
    """BeatmapSnapshot should resolve nested beatmap_tags and owner_profiles."""
    user_id = 10000001
    beatmapset_id = 1000001
    beatmap_id = 10000101

    await db.add(User, session=db_session, id=user_id)
    await db.add(Beatmapset, session=db_session, id=beatmapset_id, user_id=user_id)
    await db.add(Beatmap, session=db_session, id=beatmap_id, beatmapset_id=beatmapset_id)

    created = await db.add(
        BeatmapSnapshot,
        session=db_session,
        id=beatmap_id,
        beatmap_id=beatmap_id,
        user_id=user_id,
        snapshot_number=1,
        checksum="bm_snapshot_tags_owners_unique",
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
        url="https://osu.ppy.sh/beatmaps/10000101",
        version="Normal",
        beatmap_tags=[
            {"id": 1, "name": "style/symmetrical", "ruleset_id": 0, "description": "Symmetrical design"},
            {"id": 2, "name": "genre/electronic", "ruleset_id": 0, "description": "Electronic music"},
        ],
        owner_profiles=[
            {
                "user_id": user_id,
                "username": "testmapper",
                "avatar_url": "https://a.ppy.sh/10000001?1748873352.gif",
                "country_code": "US",
            },
        ],
    )

    assert created.checksum == "bm_snapshot_tags_owners_unique"

    tags = await db.get_many(BeatmapTag, session=db_session)
    tag_names = {t.name for t in tags}
    assert tag_names == {"style/symmetrical", "genre/electronic"}

    profile = await db.get(Profile, session=db_session, user_id=user_id)
    assert profile is not None
    assert profile.username == "testmapper"


@pytest.mark.asyncio
async def test_beatmapset_snapshot_with_beatmap_snapshots(db, db_session):
    """BeatmapsetSnapshot should resolve nested beatmap_snapshots via M2M."""
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
async def test_resolve_beatmapset_snapshot_by_checksum(db, db_session):
    """BeatmapsetSnapshot should be resolved by unique checksum."""
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
async def test_resolve_beatmap_snapshot_by_checksum(db, db_session):
    """BeatmapSnapshot should be resolved by unique checksum."""
    user_id = 10000004
    beatmapset_id = 1000004
    beatmap_id = 10000104

    await db.add(User, session=db_session, id=user_id)
    await db.add(Beatmapset, session=db_session, id=beatmapset_id, user_id=user_id)
    await db.add(Beatmap, session=db_session, id=beatmap_id, beatmapset_id=beatmapset_id)

    snapshot1 = await db.add(
        BeatmapSnapshot,
        session=db_session,
        id=beatmap_id,
        beatmap_id=beatmap_id,
        user_id=user_id,
        snapshot_number=1,
        checksum="unique_bm_chk_10000004",
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
        url="https://osu.ppy.sh/beatmaps/10000104",
        version="Normal",
    )

    snapshot2 = await db.add(
        BeatmapSnapshot,
        session=db_session,
        id=beatmap_id,
        beatmap_id=beatmap_id,
        user_id=user_id,
        snapshot_number=1,
        checksum="unique_bm_chk_10000004",
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
        url="https://osu.ppy.sh/beatmaps/10000104_different",
        version="Insane",
    )

    assert snapshot1 is snapshot2
    assert snapshot1.accuracy == 4.0
    assert snapshot1.bpm == 190.0


@pytest.mark.asyncio
async def test_resolve_beatmapset_cross_session(db, db_session):
    """Beatmapset from one session should be resolvable in another session."""
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
async def test_multiple_beatmap_snapshots_same_beatmap(db, db_session):
    """Multiple BeatmapSnapshots with same beatmap_id but different snapshot_number."""
    user_id = 10000006
    beatmapset_id = 1000006
    beatmap_id = 10000106

    await db.add(User, session=db_session, id=user_id)
    await db.add(Beatmapset, session=db_session, id=beatmapset_id, user_id=user_id)
    await db.add(Beatmap, session=db_session, id=beatmap_id, beatmapset_id=beatmapset_id)

    snapshot1 = await db.add(
        BeatmapSnapshot,
        session=db_session,
        id=10000001,
        beatmap_id=beatmap_id,
        user_id=user_id,
        snapshot_number=1,
        checksum="multi_snap_bm_1_unique",
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
        url="https://osu.ppy.sh/beatmaps/10000106",
        version="Normal",
    )

    snapshot2 = await db.add(
        BeatmapSnapshot,
        session=db_session,
        id=10000002,
        beatmap_id=beatmap_id,
        user_id=user_id,
        snapshot_number=2,
        checksum="multi_snap_bm_2_unique",
        accuracy=4.5,
        ar=5.5,
        beatmapset_id=beatmapset_id,
        bpm=190.0,
        count_circles=95,
        count_sliders=210,
        count_spinners=2,
        cs=3.2,
        difficulty_rating=2.5,
        drain=4.2,
        failtimes={"exit": [], "fail": []},
        hit_length=225,
        is_scoreable=False,
        last_updated="2018-01-01T00:00:00+00:00",
        max_combo=720,
        mode="osu",
        mode_int=0,
        passcount=5,
        playcount=20,
        ranked=-2,
        status="graveyard",
        total_length=241,
        url="https://osu.ppy.sh/beatmaps/10000106",
        version="Hard",
    )

    snapshot3 = await db.add(
        BeatmapSnapshot,
        session=db_session,
        id=10000003,
        beatmap_id=beatmap_id,
        user_id=user_id,
        snapshot_number=3,
        checksum="multi_snap_bm_3_unique",
        accuracy=5.0,
        ar=6.0,
        beatmapset_id=beatmapset_id,
        bpm=190.0,
        count_circles=100,
        count_sliders=220,
        count_spinners=3,
        cs=3.5,
        difficulty_rating=3.0,
        drain=4.5,
        failtimes={"exit": [], "fail": []},
        hit_length=230,
        is_scoreable=True,
        last_updated="2019-01-01T00:00:00+00:00",
        max_combo=750,
        mode="osu",
        mode_int=0,
        passcount=50,
        playcount=100,
        ranked=1,
        status="ranked",
        total_length=241,
        url="https://osu.ppy.sh/beatmaps/10000106",
        version="Insane",
    )

    assert snapshot1 is not snapshot2
    assert snapshot2 is not snapshot3
    assert snapshot1 is not snapshot3

    snapshots = await db.get_many(BeatmapSnapshot, session=db_session, beatmap_id=beatmap_id)
    assert len(snapshots) == 3
    snapshot_numbers = {s.snapshot_number for s in snapshots}
    assert snapshot_numbers == {1, 2, 3}


@pytest.mark.asyncio
async def test_add_many_beatmapsets(db, db_session):
    """add_many should handle multiple beatmapsets with nested data."""
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


@pytest.mark.asyncio
async def test_add_many_beatmapset_snapshots(db, db_session):
    """add_many should handle multiple beatmapset snapshots with nested beatmap snapshots."""
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

    snapshots = await db.get_many(BeatmapsetSnapshot, session=db_session, beatmapset_id=beatmapset_id)
    assert len(snapshots) == 2


@pytest.mark.asyncio
async def test_resolve_bms_by_composite_unique_constraint(db, db_session):
    """BeatmapsetSnapshot should be resolved by composite unique constraint (beatmapset_id, snapshot_number)."""
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
async def test_resolve_bmsnap_by_composite_unique_constraint(db, db_session):
    """BeatmapSnapshot should be resolved by composite unique constraint (beatmap_id, snapshot_number)."""
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


@pytest.mark.asyncio
async def test_resolve_bms_cross_session(db, db_session):
    """BeatmapsetSnapshot created in one session should be resolvable in another session."""
    user_id = 10000013
    beatmapset_id = 1000013

    await db.add(User, id=user_id)
    await db.add(Beatmapset, id=beatmapset_id, user_id=user_id)

    async with db.session() as session_a:
        await db.add(
            BeatmapsetSnapshot,
            session=session_a,
            beatmapset_id=beatmapset_id,
            user_id=user_id,
            snapshot_number=1,
            checksum="cross_s_bms_u13",
            artist="CrossSessionArtist",
            artist_unicode="CrossSessionArtist",
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
            preview_url="//b.ppy.sh/preview/1000013.mp3",
            ranked=-2,
            rating=0,
            ratings=[0] * 10,
            source="Test",
            spotlight=False,
            status="graveyard",
            storyboard=False,
            submitted_date="2017-06-07T03:50:21+00:00",
            tags="cross_session",
            title="Cross Session Song",
            title_unicode="Cross Session Song",
            track_id=None,
            video=False,
        )

    async with db.session() as session_b:
        resolved = await db.add(
            BeatmapsetSnapshot,
            session=session_b,
            beatmapset_id=beatmapset_id,
            user_id=user_id,
            snapshot_number=1,
            checksum="cross_s_bms_u13",
            artist="DifferentArtist",
            artist_unicode="DifferentArtist",
            availability={"download_disabled": True, "more_information": "See docs"},
            bpm=200.0,
            can_be_hyped=True,
            creator="different_creator",
            current_nominations=[{"nominator": "user1"}],
            deleted_at=None,
            description={"description": "Different"},
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
            tags="different",
            title="Different Song",
            title_unicode="Different Song",
            track_id=12345,
            video=True,
        )

        assert resolved.artist == "CrossSessionArtist"
        assert resolved.bpm == 190.0

        fetched = await db.get(BeatmapsetSnapshot, session=session_b, checksum="cross_s_bms_u13")
        assert fetched is not None
        assert fetched.artist == "CrossSessionArtist"


@pytest.mark.asyncio
async def test_resolve_bmsnap_cross_session(db, db_session):
    """BeatmapSnapshot created in one session should be resolvable in another session."""
    user_id = 10000014
    beatmapset_id = 1000014
    beatmap_id = 10000114

    await db.add(User, id=user_id)
    await db.add(Beatmapset, id=beatmapset_id, user_id=user_id)
    await db.add(Beatmap, id=beatmap_id, beatmapset_id=beatmapset_id)

    async with db.session() as session_a:
        await db.add(
            BeatmapSnapshot,
            session=session_a,
            id=beatmap_id,
            beatmap_id=beatmap_id,
            user_id=user_id,
            snapshot_number=1,
            checksum="cross_s_bmsnap_u14",
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
            url="https://osu.ppy.sh/beatmaps/10000114",
            version="Normal",
        )

    async with db.session() as session_b:
        resolved = await db.add(
            BeatmapSnapshot,
            session=session_b,
            id=beatmap_id,
            beatmap_id=beatmap_id,
            user_id=user_id,
            snapshot_number=1,
            checksum="cross_s_bmsnap_u14",
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
            url="https://osu.ppy.sh/beatmaps/10000114_different",
            version="Insane",
        )

        assert resolved.accuracy == 4.0
        assert resolved.bpm == 190.0


@pytest.mark.asyncio
async def test_bms_with_beatmapset_tags(db, db_session):
    """BeatmapsetSnapshot should resolve nested beatmapset_tags."""
    user_id = 10000015
    beatmapset_id = 1000015

    await db.add(User, session=db_session, id=user_id)
    await db.add(Beatmapset, session=db_session, id=beatmapset_id, user_id=user_id)

    bms = await db.add(
        BeatmapsetSnapshot,
        session=db_session,
        beatmapset_id=beatmapset_id,
        user_id=user_id,
        snapshot_number=1,
        checksum="bms_with_bms_tags_unique",
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
        preview_url="//b.ppy.sh/preview/1000015.mp3",
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
        beatmapset_tags=[
            {"name": "genre/electronic"},
            {"name": "style/symmetrical"},
        ],
    )

    assert bms.checksum == "bms_with_bms_tags_unique"

    await db_session.refresh(bms, attribute_names=["beatmapset_tags"])
    tag_names = {t.name for t in bms.beatmapset_tags}
    assert tag_names == {"genre/electronic", "style/symmetrical"}


@pytest.mark.asyncio
async def test_bms_with_user_profile(db, db_session):
    """BeatmapsetSnapshot should resolve nested user_profile (scalar relationship to Profile)."""
    user_id = 10000016
    beatmapset_id = 1000016

    await db.add(User, session=db_session, id=user_id)
    await db.add(Beatmapset, session=db_session, id=beatmapset_id, user_id=user_id)

    bms = await db.add(
        BeatmapsetSnapshot,
        session=db_session,
        beatmapset_id=beatmapset_id,
        user_id=user_id,
        snapshot_number=1,
        checksum="bms_with_user_profile_unique",
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
        preview_url="//b.ppy.sh/preview/1000016.mp3",
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
        user_profile={
            "user_id": user_id,
            "username": "profile_via_user_profile",
        },
    )

    assert bms.checksum == "bms_with_user_profile_unique"

    profile = await db.get(Profile, session=db_session, user_id=user_id)
    assert profile is not None
    assert profile.username == "profile_via_user_profile"


@pytest.mark.asyncio
async def test_add_many_beatmap_snapshots(db, db_session):
    """add_many should handle multiple BeatmapSnapshots."""
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
async def test_resolve_existing_bmsnap_via_bms_creation(db, db_session):
    """When creating a BeatmapsetSnapshot with nested BeatmapSnapshot dicts, existing BeatmapSnapshots should be resolved not re-created."""
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
