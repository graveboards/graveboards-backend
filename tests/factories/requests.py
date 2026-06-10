import pytest

from app.database.models import Request


def create_request_from_beatmapset_id(beatmapset_id: int, queue_id: int = 1, **kwargs) -> Request:
    """Create a Request model from a beatmapset fixture."""
    return Request(
        beatmapset_id=beatmapset_id,
        queue_id=queue_id,
        comment=kwargs.get("comment", f"Please add beatmapset {beatmapset_id}"),
        mv_checked=kwargs.get("mv_checked", False),
        status=kwargs.get("status", 0),
    )


def create_request_from_user_and_beatmapset(user_id: int, beatmapset_id: int, queue_id: int = 1, **kwargs) -> Request:
    """Create a Request model from user and beatmapset fixtures."""
    return Request(
        user_id=user_id,
        beatmapset_id=beatmapset_id,
        queue_id=queue_id,
        comment=kwargs.get("comment", "Please rank this beatmapset"),
        mv_checked=kwargs.get("mv_checked", False),
        status=kwargs.get("status", 0),
    )


@pytest.fixture
def request_factory():
    """Factory fixture for creating request instances."""
    return create_request_from_beatmapset_id
