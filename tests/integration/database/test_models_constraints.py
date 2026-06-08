import pytest
from sqlalchemy import insert
from sqlalchemy.sql import select

from app.database.models import User, Profile, Queue, Request, Beatmapset, BeatmapsetSnapshot, BeatmapsetListing


@pytest.mark.asyncio
async def test_cascade_delete_request_on_user(db_session_transaction):
    """Test that deleting User cascades to Requests."""
    db = PostgresqlDB()
    
    user = await db.add(User, session=db_session_transaction, id=1014)
    queue = await db.add(Queue, session=db_session_transaction, user_id=1014, name="Test Queue", description="Test")
    
    beatmapset_data = {
        "id": 10014,
        "user_id": 1014,
    }
    beatmapset = await db.add(Beatmapset, session=db_session_transaction, **beatmapset_data)
    
    snapshot_data = {
        "beatmapset_id": 10014,
        "user_id": 1014,
        "snapshot_number": 1,
        "checksum": "f" * 32,
        "artist": "Test",
        "artist_unicode": "Test",
        "availability": {"download_disabled": False, "more_information": None},
        "bpm": 120.0,
        "can_be_hyped": True,
        "creator": "Test",
        "current_nominations": [],
        "deleted_at": None,
        "description": {"description": "Test"},
        "discussion_enabled": True,
        "discussion_locked": False,
        "favourite_count": 0,
        "genre": None,
        "hype": None,
        "is_scoreable": True,
        "language": None,
        "last_updated": "2024-01-01T00:00:00+00:00",
        "nominations_summary": {"current": 0, "required_meta": {"main_ruleset": 0, "non_main_ruleset": 0}},
        "nsfw": False,
        "offset": 0,
        "pack_tags": [],
        "play_count": 0,
        "preview_url": "",
        "ranked": 0,
        "ranked_date": None,
        "rating": 0.0,
        "ratings": [],
        "source": "",
        "spotlight": False,
        "status": "pending",
        "storyboard": False,
        "submitted_date": "2024-01-01T00:00:00+00:00",
        "tags": "",
        "title": "Test",
        "title_unicode": "Test",
        "video": False,
    }
    beatmapset_snapshot = await db.add(BeatmapsetSnapshot, session=db_session_transaction, **snapshot_data)
    
    request_data = {
        "user_id": 1014,
        "queue_id": queue.id,
        "beatmapset_id": 10014,
        "beatmapset_snapshot_id": beatmapset_snapshot.id,
        "comment": "Test",
    }
    request = await db.add(Request, session=db_session_transaction, **request_data)
    
    await db.delete(User, session=db_session_transaction, id=1014)
    
    fetched_request = await db.get(Request, session=db_session_transaction, id=request.id)
    assert fetched_request is None
    
    result = await session.execute(
        select(Queue).where(Queue.user_id == 1014)
    )
    fetched_queue = result.scalars().first()
    assert fetched_queue is None
    
    result = await session.execute(
        select(Beatmapset).where(Beatmapset.user_id == 1014)
    )
    fetched_beatmapset = result.scalars().first()
    assert fetched_beatmapset is None
    
    result = await session.execute(
        select(BeatmapsetSnapshot).where(BeatmapsetSnapshot.user_id == 1014)
    )
    fetched_snapshot = result.scalars().first()
    assert fetched_snapshot is None
    
    result = await session.execute(
        select(BeatmapsetListing).where(BeatmapsetListing.beatmapset_id == 10014)
    )
    fetched_listing = result.scalars().first()
    assert fetched_listing is None
