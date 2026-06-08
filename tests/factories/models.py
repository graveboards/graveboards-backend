from datetime import datetime, timedelta
from typing import Optional

import pytest

from app.database.models import User, Profile, Queue, Request, Beatmap, Beatmapset
from app.database.schemas import ProfileSchema, QueueSchema, RequestSchema


def create_user(**kwargs) -> User:
    """Create a user model instance with defaults."""
    return User(
        id=kwargs.get("id", 12345),
        profile=kwargs.get("profile"),
        roles=kwargs.get("roles", []),
        scores=kwargs.get("scores", []),
        api_keys=kwargs.get("api_keys", []),
        tokens=kwargs.get("tokens", []),
        queues=kwargs.get("queues", []),
        requests=kwargs.get("requests", []),
        beatmapsets=kwargs.get("beatmapsets", []),
        score_fetcher_task=kwargs.get("score_fetcher_task"),
        profile_fetcher_task=kwargs.get("profile_fetcher_task"),
    )


def create_profile(user_id: Optional[int] = None, **kwargs) -> Profile:
    """Create a profile model instance with defaults."""
    return Profile(
        id=kwargs.get("id"),
        user_id=user_id or kwargs.get("user_id", 12345),
        updated_at=kwargs.get("updated_at"),
        is_restricted=kwargs.get("is_restricted", False),
        username=kwargs.get("username", "testuser"),
        avatar_url=kwargs.get("avatar_url", "https://example.com/avatar.png"),
        country_code=kwargs.get("country_code", "US"),
        join_date=kwargs.get("join_date", datetime.now() - timedelta(days=365)),
        is_active=kwargs.get("is_active", True),
        is_bot=kwargs.get("is_bot", False),
        is_deleted=kwargs.get("is_deleted", False),
        is_online=kwargs.get("is_online", True),
        is_supporter=kwargs.get("is_supporter", False),
        **kwargs,
    )


def create_queue(user_id: Optional[int] = None, **kwargs) -> Queue:
    """Create a queue model instance with defaults."""
    return Queue(
        id=kwargs.get("id"),
        user_id=user_id or kwargs.get("user_id", 12345),
        name=kwargs.get("name", "Test Queue"),
        description=kwargs.get("description", "A test queue for beatmaps"),
        created_at=kwargs.get("created_at"),
        updated_at=kwargs.get("updated_at"),
        is_open=kwargs.get("is_open", True),
        visibility=kwargs.get("visibility", 0),
        managers=kwargs.get("managers", []),
        requests=kwargs.get("requests", []),
        user_profile=kwargs.get("user_profile"),
        manager_profiles=kwargs.get("manager_profiles", []),
    )


def create_request(queue_id: Optional[int] = None, beatmapset_id: Optional[int] = None, **kwargs) -> Request:
    """Create a request model instance with defaults."""
    return Request(
        id=kwargs.get("id"),
        user_id=kwargs.get("user_id", 12345),
        beatmapset_id=beatmapset_id or kwargs.get("beatmapset_id", 100),
        beatmapset_snapshot_id=kwargs.get("beatmapset_snapshot_id", 1),
        queue_id=queue_id or kwargs.get("queue_id", 1),
        comment=kwargs.get("comment", "Please add this beatmap"),
        mv_checked=kwargs.get("mv_checked", False),
        created_at=kwargs.get("created_at"),
        updated_at=kwargs.get("updated_at"),
        status=kwargs.get("status", 0),
        beatmapset_snapshot=kwargs.get("beatmapset_snapshot"),
        user_profile=kwargs.get("user_profile"),
        queue=kwargs.get("queue"),
    )


@pytest.fixture
def user_factory():
    """Factory fixture for creating user instances."""
    return create_user


@pytest.fixture
def profile_factory():
    """Factory fixture for creating profile instances."""
    return create_profile


@pytest.fixture
def queue_factory():
    """Factory fixture for creating queue instances."""
    return create_queue


@pytest.fixture
def request_factory():
    """Factory fixture for creating request instances."""
    return create_request


def create_beatmap(beatmapset_id: Optional[int] = None, **kwargs) -> Beatmap:
    """Create a beatmap model instance with defaults."""
    return Beatmap(
        id=kwargs.get("id", 116383),
        beatmapset_id=beatmapset_id or kwargs.get("beatmapset_id", 35965),
    )


def create_beatmapset(user_id: Optional[int] = None, **kwargs) -> Beatmapset:
    """Create a beatmapset model instance with defaults."""
    return Beatmapset(
        id=kwargs.get("id", 35965),
        user_id=user_id or kwargs.get("user_id", 12345),
    )


@pytest.fixture
def beatmap_factory():
    """Factory fixture for creating beatmap instances."""
    return create_beatmap


@pytest.fixture
def beatmapset_factory():
    """Factory fixture for creating beatmapset instances."""
    return create_beatmapset
