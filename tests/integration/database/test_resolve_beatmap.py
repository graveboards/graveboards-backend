from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from app.database.db import PostgresqlDB


@pytest.mark.asyncio
async def test_beatmap_snapshot_with_tags_and_owners(db: PostgresqlDB, db_session: Any) -> None:
    """BeatmapSnapshot should resolve nested beatmap_tags and owner_profiles."""
    from app.database.models import (
        Beatmap,
        Beatmapset,
        BeatmapSnapshot,
        BeatmapTag,
        Profile,
        User,
    )

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
            {
                "id": 1,
                "name": "style/symmetrical",
                "ruleset_id": 0,
                "description": "Symmetrical design",
            },
            {
                "id": 2,
                "name": "genre/electronic",
                "ruleset_id": 0,
                "description": "Electronic music",
            },
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

    tags_result = await db.get_many(BeatmapTag, session=db_session)
    tags = tags_result if isinstance(tags_result, list) else tags_result[0]
    tag_names = {t.name for t in tags}
    assert tag_names == {"style/symmetrical", "genre/electronic"}

    profile = await db.get(Profile, session=db_session, user_id=user_id)
    assert profile is not None
    assert profile.username == "testmapper"


@pytest.mark.asyncio
async def test_resolve_beatmap_snapshot_by_checksum(db: PostgresqlDB, db_session: Any) -> None:
    """BeatmapSnapshot should be resolved by unique checksum."""
    from app.database.models import (
        Beatmap,
        Beatmapset,
        BeatmapSnapshot,
        User,
    )

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
async def test_multiple_beatmap_snapshots_same_beatmap(db: PostgresqlDB, db_session: Any) -> None:
    """Multiple BeatmapSnapshots with same beatmap_id but different snapshot_number."""
    from app.database.models import (
        Beatmap,
        Beatmapset,
        BeatmapSnapshot,
        User,
    )

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
