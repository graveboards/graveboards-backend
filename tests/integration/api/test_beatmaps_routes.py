import pytest

from app.database.models import Beatmap, Beatmapset


@pytest.mark.integration
@pytest.mark.asyncio
async def test_beatmap_model_creation():
    beatmap = Beatmap(
        id=116383,
        beatmapset_id=35965
    )

    assert beatmap.id == 116383
    assert beatmap.beatmapset_id == 35965


@pytest.mark.integration
@pytest.mark.asyncio
async def test_beatmap_relationships():
    beatmap = Beatmap(
        id=116383,
        beatmapset_id=35965
    )

    assert hasattr(beatmap, 'beatmapset')
    assert hasattr(beatmap, 'snapshots')


@pytest.mark.integration
@pytest.mark.asyncio
async def test_beatmap_num_snapshots():
    beatmap = Beatmap(
        id=116383,
        beatmapset_id=35965
    )

    assert hasattr(beatmap, 'num_snapshots')


@pytest.mark.integration
@pytest.mark.asyncio
async def test_beatmapset_model_creation():
    beatmapset = Beatmapset(
        id=35965,
        user_id=12345678
    )

    assert beatmapset.id == 35965
    assert beatmapset.user_id == 12345678


@pytest.mark.integration
@pytest.mark.asyncio
async def test_beatmapset_relationships():
    beatmapset = Beatmapset(
        id=35965,
        user_id=12345678
    )

    assert hasattr(beatmapset, 'beatmaps')
    assert hasattr(beatmapset, 'snapshots')


@pytest.mark.integration
@pytest.mark.asyncio
async def test_beatmapset_num_snapshots():
    beatmapset = Beatmapset(
        id=35965,
        user_id=12345678
    )

    assert hasattr(beatmapset, 'num_snapshots')


@pytest.mark.integration
@pytest.mark.asyncio
async def test_beatmap_beatmapset_relationship():
    beatmapset = Beatmapset(
        id=35965,
        user_id=12345678
    )

    beatmap = Beatmap(
        id=116383,
        beatmapset_id=beatmapset.id
    )

    assert beatmap.beatmapset_id == beatmapset.id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_beatmapset_beatmap_relationship():
    beatmapset = Beatmapset(
        id=35965,
        user_id=12345678
    )

    beatmap1 = Beatmap(
        id=116383,
        beatmapset_id=beatmapset.id
    )

    beatmap2 = Beatmap(
        id=116384,
        beatmapset_id=beatmapset.id
    )

    assert beatmap1.beatmapset_id == beatmap2.beatmapset_id
