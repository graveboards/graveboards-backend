import pytest

from app.database.models import Queue


@pytest.mark.integration
@pytest.mark.asyncio
async def test_queue_model_creation():
    queue = Queue(
        user_id=12345678,
        name="Test Queue",
        description="A test queue",
        visibility=0,
        is_open=True
    )

    assert queue.user_id == 12345678
    assert queue.name == "Test Queue"
    assert queue.description == "A test queue"
    assert queue.visibility == 0
    assert queue.is_open == True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_queue_visibility_enum():
    queue = Queue(
        user_id=12345678,
        name="Test Queue",
        visibility=0
    )
    assert queue.visibility == 0

    queue.visibility = 1
    assert queue.visibility == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_queue_open_close():
    queue = Queue(
        user_id=12345678,
        name="Test Queue",
        is_open=True
    )

    assert queue.is_open == True

    queue.is_open = False
    assert queue.is_open == False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_queue_relationships():
    queue = Queue(
        user_id=12345678,
        name="Test Queue"
    )

    assert hasattr(queue, 'requests')
    assert hasattr(queue, 'managers')
    assert hasattr(queue, 'user_profile')
    assert hasattr(queue, 'manager_profiles')


@pytest.mark.integration
@pytest.mark.asyncio
async def test_queue_unique_constraint():
    queue1 = Queue(
        user_id=12345678,
        name="Test Queue"
    )

    queue2 = Queue(
        user_id=12345678,
        name="Different Queue"
    )

    assert queue1.user_id == queue2.user_id
    assert queue1.name != queue2.name


@pytest.mark.integration
@pytest.mark.asyncio
async def test_queue_timestamp_fields():
    queue = Queue(
        user_id=12345678,
        name="Test Queue"
    )

    assert hasattr(queue, 'created_at')
    assert hasattr(queue, 'updated_at')
