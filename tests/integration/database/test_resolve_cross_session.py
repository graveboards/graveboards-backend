from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from app.database.db import PostgresqlDB


@pytest.mark.asyncio
async def test_resolve_bms_cross_session(db: PostgresqlDB, db_session: Any) -> None:
    """BeatmapsetSnapshot created in one session should be resolvable in another session."""
    from app.database.models import (
        Beatmapset,
        BeatmapsetSnapshot,
        User,
    )

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
async def test_resolve_bmsnap_cross_session(db: PostgresqlDB, db_session: Any) -> None:
    """BeatmapSnapshot created in one session should be resolvable in another session."""
    from app.database.models import (
        Beatmap,
        Beatmapset,
        BeatmapSnapshot,
        User,
    )

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
