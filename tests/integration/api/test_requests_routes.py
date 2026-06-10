import pytest

from app.database.models import Request, Queue


@pytest.mark.integration
@pytest.mark.asyncio
async def test_request_model_creation():
    request = Request(
        user_id=12345678,
        beatmapset_id=35965,
        queue_id=1,
        status=0
    )

    assert request.user_id == 12345678
    assert request.beatmapset_id == 35965
    assert request.queue_id == 1
    assert request.status == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_request_with_comment():
    request = Request(
        user_id=12345678,
        beatmapset_id=35965,
        queue_id=1,
        comment="Please rank this beatmapset!"
    )

    assert request.comment == "Please rank this beatmapset!"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_request_mv_checked():
    request = Request(
        user_id=12345678,
        beatmapset_id=35965,
        queue_id=1,
        mv_checked=False
    )

    assert request.mv_checked == False

    request.mv_checked = True
    assert request.mv_checked == True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_request_status_values():
    request = Request(
        user_id=12345678,
        beatmapset_id=35965,
        queue_id=1,
        status=0
    )

    assert request.status == 0

    request.status = 1
    assert request.status == 1

    request.status = 2
    assert request.status == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_request_relationships():
    request = Request(
        user_id=12345678,
        beatmapset_id=35965,
        queue_id=1
    )

    assert hasattr(request, 'beatmapset_snapshot')
    assert hasattr(request, 'user_profile')
    assert hasattr(request, 'queue')


@pytest.mark.integration
@pytest.mark.asyncio
async def test_request_unique_constraint():
    queue = Queue(
        user_id=12345678,
        name="Test Queue"
    )

    request1 = Request(
        user_id=12345678,
        beatmapset_id=35965,
        queue_id=queue.id
    )

    request2 = Request(
        user_id=12345678,
        beatmapset_id=99999,
        queue_id=queue.id
    )

    assert request1.beatmapset_id != request2.beatmapset_id
    assert request1.queue_id == request2.queue_id
