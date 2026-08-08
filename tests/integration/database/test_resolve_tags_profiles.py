from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from app.database.db import PostgresqlDB


@pytest.mark.asyncio
async def test_bms_with_beatmapset_tags(db: PostgresqlDB, db_session: Any) -> None:
    """BeatmapsetSnapshot should resolve nested beatmapset_tags."""
    from app.database.models import (
        Beatmapset,
        BeatmapsetSnapshot,
        User,
    )

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
async def test_bms_with_user_profile(db: PostgresqlDB, db_session: Any) -> None:
    """BeatmapsetSnapshot should resolve nested user_profile (scalar relationship to Profile)."""
    from app.database.models import (
        Beatmapset,
        BeatmapsetSnapshot,
        Profile,
        User,
    )

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
