import pytest

from app.database.models import Queue
from tests.fixtures.osu import load_user


def create_queue_from_user_id(user_id: int, name: str = "Test Queue", **kwargs) -> Queue:
    """Create a Queue model from a user fixture."""
    return Queue(
        user_id=user_id,
        name=name,
        description=kwargs.get("description", f"Queue created by user {user_id}"),
        is_open=kwargs.get("is_open", True),
        visibility=kwargs.get("visibility", 0),
    )


@pytest.fixture
def queue_factory():
    """Factory fixture for creating queue instances."""
    return create_queue_from_user_id
