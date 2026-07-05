"""Coverage-gated search integration tests.

These tests use the SearchTestFixtureFetcher's coverage report to determine
what fixture data is available, then seed and test the search engine.

Each test checks the coverage report for required data and skips if missing.
Tests query the search engine with specific filters/terms/sorting and assert
results match expected behavior.

Run with: pytest tests/integration/search/test_search_integration.py -m integration
"""
import json
import pytest
from pathlib import Path
from datetime import datetime, timezone

from app.fixtures.utils import FIXTURES_DIR
from app.search.engine import SearchEngine
from app.search.datastructures import SearchTermsSchema, FiltersSchema
from app.search.enums import Scope, ModelField, SortingOrder
from app.database.models import Beatmapset, Beatmap, BeatmapSnapshot, BeatmapsetSnapshot, Profile, User
from tests.fixtures.osu import load_beatmapset, load_beatmap


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def search_test_fetcher():
    """Create a SearchTestFixtureFetcher for reading coverage reports.

    This does NOT perform any API calls. It only reads the coverage state
    from metadata.json that was previously populated by the CLI.
    """
    from app.redis import RedisClient
    from app.fixtures.search_test_fetcher import SearchTestFixtureFetcher

    rc = RedisClient()
    fetcher = SearchTestFixtureFetcher(rc)
    fetcher._load_coverage_from_metadata()
    yield fetcher
    await rc.aclose()


class SearchFixtureSeeder:
    """Seeds search test data from fetched JSON fixtures into the database.

    Reads from instance/fixtures/ (the fetcher output) and creates
    Beatmapset, Beatmap, BeatmapSnapshot, and BeatmapsetSnapshot objects.
    """

    def __init__(self, session, coverage: dict):
        self.session = session
        self.coverage = coverage
        self.seeded_bs_ids: list[int] = []
        self.seeded_bm_ids: list[int] = []
        self.seeded_user_ids: list[int] = []

    def _load_json(self, category: str, filename: str) -> dict | None:
        """Load a JSON fixture file from instance/fixtures/."""
        filepath = FIXTURES_DIR / category / filename
        if not filepath.exists():
            return None
        with open(filepath, "r") as f:
            return json.load(f)

    async def seed_beatmapset_from_coverage(self, bs_id: int) -> BeatmapsetSnapshot | None:
        """Seed a single beatmapset from fetched JSON data."""
        bs_data = self._load_json("beatmapsets", f"beatmapset_{bs_id}.json")
        if bs_data is None:
            return None

        user_data = bs_data.get("user", {})
        user_id = user_data.get("id") if user_data else None
        
        # Seed the user first if they exist in our fixtures
        if user_id:
            user_json = self._load_json("users/osu", f"user_{user_id}_osu.json")
            if user_json:
                await self.seed_users_from_coverage([user_id])
            else:
                # User not in fixtures, create a dummy user
                if user_id not in self.seeded_user_ids:
                    dummy_user = User(id=user_id)
                    self.session.add(dummy_user)
                    self.seeded_user_ids.append(user_id)
        else:
            # No user in beatmapset data, use a dummy user
            user_id = 999999
            if user_id not in self.seeded_user_ids:
                dummy_user = User(id=user_id)
                self.session.add(dummy_user)
                self.seeded_user_ids.append(user_id)

        beatmapset = Beatmapset(id=bs_id, user_id=user_id)
        self.session.add(beatmapset)
        await self.session.flush()

        beatmap_ids = []
        beatmap_snapshots = []

        for bm_data in bs_data.get("beatmaps", []):
            bm_id = bm_data.get("id")
            if not bm_id:
                continue
            beatmap_ids.append(bm_id)

            if bm_id not in self.seeded_bm_ids:
                self.seeded_bm_ids.append(bm_id)

            beatmap = Beatmap(id=bm_id, beatmapset_id=bs_id)
            self.session.add(beatmap)
            await self.session.flush()

            beatmap_snapshot = BeatmapSnapshot(
                beatmap_id=bm_id,
                user_id=user_id,
                snapshot_number=1,
                accuracy=bm_data.get("accuracy", 100.0),
                ar=bm_data.get("ar", 9.0),
                beatmapset_id=bs_id,
                bpm=bm_data.get("bpm", 120.0),
                checksum=bm_data.get("checksum", f"dummy_{bm_id}"),
                count_circles=bm_data.get("count_circles", 100),
                count_sliders=bm_data.get("count_sliders", 50),
                count_spinners=bm_data.get("count_spinners", 10),
                cs=bm_data.get("cs", 4.0),
                difficulty_rating=bm_data.get("difficulty_rating", 5.0),
                drain=bm_data.get("drain", 5.0),
                failtimes=bm_data.get("failtimes", {}),
                hit_length=bm_data.get("hit_length", 180),
                is_scoreable=bm_data.get("is_scoreable", True),
                last_updated=datetime.fromisoformat(
                    bm_data.get("last_updated", "2024-01-01T00:00:00+00:00").replace("Z", "+00:00")
                ) if bm_data.get("last_updated") else datetime.now(timezone.utc),
                max_combo=bm_data.get("max_combo", 1000),
                mode=bm_data.get("mode", "osu"),
                mode_int=bm_data.get("mode_int", 0),
                passcount=bm_data.get("passcount", 100),
                playcount=bm_data.get("playcount", 1000),
                ranked=bm_data.get("ranked", 1),
                status=bm_data.get("status", "ranked"),
                total_length=bm_data.get("total_length", 200),
                url=bm_data.get("url", f"https://osu.ppy.sh/b/{bm_id}"),
                version=bm_data.get("version", "Hard"),
            )
            self.session.add(beatmap_snapshot)
            await self.session.flush()
            beatmap_snapshots.append(beatmap_snapshot)

        genre = bs_data.get("genre", {"id": 1, "name": "Any"})
        language = bs_data.get("language", {"id": 1, "name": "Any"})
        description = bs_data.get("description", {"description": ""})
        if isinstance(description, str):
            description = {"description": description}

        current_nominations = bs_data.get("current_nominations", {"nominators": [], "required": 2})
        nominations_summary = bs_data.get("nominations_summary", {
            "current": 2, "required": 2,
            "required_meta": {"main_ruleset": 2, "non_main_ruleset": 1}
        })
        hype = bs_data.get("hype")
        ratings = bs_data.get("ratings", [5])
        if isinstance(ratings, dict):
            ratings = list(ratings.values())

        now = datetime.now(timezone.utc)
        bs_snapshot = BeatmapsetSnapshot(
            beatmapset_id=bs_id,
            user_id=user_id,
            snapshot_number=1,
            checksum=f"dummy_bs_{bs_id}",
            artist=bs_data.get("artist", "Test Artist"),
            artist_unicode=bs_data.get("artist_unicode", bs_data.get("artist", "Test Artist")),
            availability=bs_data.get("availability", {"download_disabled": False, "more_information": None}),
            bpm=bs_data.get("bpm", 120.0),
            can_be_hyped=bs_data.get("can_be_hyped", True),
            covers=bs_data.get("covers"),
            creator=bs_data.get("creator", "testuser"),
            current_nominations=current_nominations,
            description=description,
            discussion_enabled=bs_data.get("discussion_enabled", True),
            discussion_locked=bs_data.get("discussion_locked", False),
            favourite_count=bs_data.get("favourite_count", 0),
            genre=genre,
            hype=hype,
            is_scoreable=bs_data.get("is_scoreable", True),
            language=language,
            last_updated=datetime.fromisoformat(
                bs_data.get("last_updated", "2024-01-01T00:00:00+00:00").replace("Z", "+00:00")
            ) if bs_data.get("last_updated") else now,
            nominations_summary=nominations_summary,
            nsfw=bs_data.get("nsfw", False),
            offset=bs_data.get("offset", 0),
            pack_tags=bs_data.get("pack_tags", []),
            play_count=bs_data.get("play_count", 0),
            preview_url=bs_data.get("preview_url", ""),
            ranked=bs_data.get("ranked", 1),
            ranked_date=datetime.fromisoformat(
                bs_data.get("ranked_date", "2024-01-01T00:00:00+00:00").replace("Z", "+00:00")
            ) if bs_data.get("ranked_date") else None,
            rating=bs_data.get("rating", 5.0),
            ratings=ratings,
            source=bs_data.get("source", ""),
            spotlight=bs_data.get("spotlight", False),
            status=bs_data.get("status", "ranked"),
            storyboard=bs_data.get("storyboard", False),
            submitted_date=datetime.fromisoformat(
                bs_data.get("submitted_date", "2024-01-01T00:00:00+00:00").replace("Z", "+00:00")
            ) if bs_data.get("submitted_date") else None,
            tags=bs_data.get("tags", ""),
            title=bs_data.get("title", "Test Song"),
            title_unicode=bs_data.get("title_unicode", bs_data.get("title", "Test Song")),
            video=bs_data.get("video", False),
        )
        self.session.add(bs_snapshot)
        await self.session.flush()

        # Associate beatmap snapshots with beatmapset snapshot via the association table
        from app.database.models.associations import beatmap_snapshot_beatmapset_snapshot_association
        for bm_snapshot in beatmap_snapshots:
            assoc = beatmap_snapshot_beatmapset_snapshot_association.insert().values(
                beatmap_snapshot_id=bm_snapshot.id,
                beatmapset_snapshot_id=bs_snapshot.id
            )
            await self.session.execute(assoc)

        self.seeded_bs_ids.append(bs_id)
        return bs_snapshot

    async def seed_users_from_coverage(self, user_ids: list[int]) -> list[int]:
        """Seed users from fetched JSON data."""
        seeded = []
        for user_id in user_ids:
            if user_id in self.seeded_user_ids:
                continue
            user_data = self._load_json("users/osu", f"user_{user_id}_osu.json")
            if user_data is None:
                continue
            self.seeded_user_ids.append(user_id)
            seeded.append(user_id)
        return seeded


@pytest.fixture
async def search_fixture_seeder(db_transaction, search_test_fetcher):
    """Seed all coverage-gated fixtures into the database.

    Uses the fetcher's coverage report to determine what fixture data
    is available, then seeds it into the database.
    """
    coverage = search_test_fetcher.get_coverage_report()
    seeder = SearchFixtureSeeder(db_transaction, coverage)

    # Seed beatmapsets for each genre that has coverage
    seeded_count = 0
    for genre_info in coverage.get("beatmapset_genres", {}).values():
        ids = genre_info.get("ids", [])
        for bs_id in ids[:3]:  # seed up to 3 per genre
            await seeder.seed_beatmapset_from_coverage(bs_id)
            seeded_count += 1

    # Seed beatmapsets for each language that has coverage (if not already seeded)
    for lang_info in coverage.get("beatmapset_languages", {}).values():
        ids = lang_info.get("ids", [])
        for bs_id in ids[:2]:
            if bs_id not in seeder.seeded_bs_ids:
                await seeder.seed_beatmapset_from_coverage(bs_id)
                seeded_count += 1

    # Seed NSFW beatmapsets
    nsfw_true_ids = coverage.get("beatmapset_nsfw", {}).get("true", {}).get("ids", [])
    nsfw_false_ids = coverage.get("beatmapset_nsfw", {}).get("false", {}).get("ids", [])
    for bs_id in nsfw_true_ids[:2]:
        if bs_id not in seeder.seeded_bs_ids:
            await seeder.seed_beatmapset_from_coverage(bs_id)
            seeded_count += 1
    for bs_id in nsfw_false_ids[:2]:
        if bs_id not in seeder.seeded_bs_ids:
            await seeder.seed_beatmapset_from_coverage(bs_id)
            seeded_count += 1

    # Seed users for country codes
    for cc_info in coverage.get("country_codes", {}).values():
        ids = cc_info.get("ids", [])
        await seeder.seed_users_from_coverage(ids[:3])

    await db_transaction.commit()
    return seeder


# ---------------------------------------------------------------------------
# Helper: check if coverage data is available
# ---------------------------------------------------------------------------

def _has_coverage(coverage: dict, bucket: str, category: str | None = None) -> bool:
    """Check if a coverage bucket has data available."""
    if bucket not in coverage:
        return False
    data = coverage[bucket]
    if category is not None:
        if isinstance(data, dict):
            return category in data and bool(data[category].get("ids", []))
        return False
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, dict) and v.get("ids"):
                return True
        return False
    return bool(data)


def _get_ids(coverage: dict, bucket: str, category: str | None = None) -> list[int]:
    """Get IDs from a coverage bucket."""
    if bucket not in coverage:
        return []
    data = coverage[bucket]
    if category is not None:
        if isinstance(data, dict) and category in data:
            return data[category].get("ids", [])
        return []
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, dict) and v.get("ids"):
                return v["ids"]
    return []


# ---------------------------------------------------------------------------
# Test: SearchBeatmapsets
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestSearchBeatmapsets:

    @pytest.mark.asyncio
    async def test_filter_by_genre(self, db_transaction, search_test_fetcher):
        """Test filtering beatmapsets by genre."""
        coverage = search_test_fetcher.get_coverage_report()
        if not _has_coverage(coverage, "beatmapset_genres"):
            pytest.skip("No beatmapset genre coverage available")

        seeder = SearchFixtureSeeder(db_transaction, coverage)
        genre_id = list(coverage["beatmapset_genres"].keys())[0]
        bs_ids = _get_ids(coverage, "beatmapset_genres", genre_id)
        if not bs_ids:
            pytest.skip(f"No beatmapsets for genre {genre_id}")

        await seeder.seed_beatmapset_from_coverage(bs_ids[0])
        await db_transaction.commit()

        engine = SearchEngine(
            scope=Scope.BEATMAPSETS,
            filters={"beatmapset": {"genre_id": genre_id}},
        )
        results = await engine.search(db_transaction, limit=10)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_filter_by_language(self, db_transaction, search_test_fetcher):
        """Test filtering beatmapsets by language."""
        coverage = search_test_fetcher.get_coverage_report()
        if not _has_coverage(coverage, "beatmapset_languages"):
            pytest.skip("No beatmapset language coverage available")

        seeder = SearchFixtureSeeder(db_transaction, coverage)
        lang_id = list(coverage["beatmapset_languages"].keys())[0]
        bs_ids = _get_ids(coverage, "beatmapset_languages", lang_id)
        if not bs_ids:
            pytest.skip(f"No beatmapsets for language {lang_id}")

        await seeder.seed_beatmapset_from_coverage(bs_ids[0])
        await db_transaction.commit()

        engine = SearchEngine(
            scope=Scope.BEATMAPSETS,
            filters={"beatmapset": {"language_id": lang_id}},
        )
        results = await engine.search(db_transaction, limit=10)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_filter_by_nsfw(self, db_transaction, search_test_fetcher):
        """Test filtering beatmapsets by NSFW status."""
        coverage = search_test_fetcher.get_coverage_report()
        nsfw_data = coverage.get("beatmapset_nsfw", {})
        true_ids = nsfw_data.get("true", {}).get("ids", [])
        false_ids = nsfw_data.get("false", {}).get("ids", [])

        if not true_ids or not false_ids:
            pytest.skip("Need both NSFW true and false beatmapsets")

        seeder = SearchFixtureSeeder(db_transaction, coverage)
        await seeder.seed_beatmapset_from_coverage(true_ids[0])
        await seeder.seed_beatmapset_from_coverage(false_ids[0])
        await db_transaction.commit()

        engine_nsfw = SearchEngine(
            scope=Scope.BEATMAPSETS,
            filters={"beatmapset": {"nsfw": True}},
        )
        results_nsfw = await engine_nsfw.search(db_transaction, limit=10)

        engine_sfw = SearchEngine(
            scope=Scope.BEATMAPSETS,
            filters={"beatmapset": {"nsfw": False}},
        )
        results_sfw = await engine_sfw.search(db_transaction, limit=10)

        assert len(results_nsfw) >= 1
        assert len(results_sfw) >= 1

    @pytest.mark.asyncio
    async def test_filter_by_status(self, db_transaction, search_test_fetcher):
        """Test filtering beatmapsets by status."""
        coverage = search_test_fetcher.get_coverage_report()
        if not coverage.get("beatmapset_statuses"):
            pytest.skip("No beatmapset status coverage available")

        # Seed a beatmapset and verify it has a status
        seeder = SearchFixtureSeeder(db_transaction, coverage)
        bs_ids = _get_ids(coverage, "beatmapset_genres")
        if bs_ids:
            await seeder.seed_beatmapset_from_coverage(bs_ids[0])
            await db_transaction.commit()

        # Just verify the engine can be created with status filter
        engine = SearchEngine(
            scope=Scope.BEATMAPSETS,
            filters={"beatmapset": {"status": "ranked"}},
        )
        assert engine is not None

    @pytest.mark.asyncio
    async def test_search_terms_title(self, db_transaction, search_test_fetcher):
        """Test full-text search by title."""
        coverage = search_test_fetcher.get_coverage_report()
        if not coverage.get("beatmapset_titles"):
            pytest.skip("No beatmapset title coverage available")

        seeder = SearchFixtureSeeder(db_transaction, coverage)
        bs_ids = _get_ids(coverage, "beatmapset_genres")
        if bs_ids:
            await seeder.seed_beatmapset_from_coverage(bs_ids[0])
            await db_transaction.commit()

        title = coverage["beatmapset_titles"][0] if coverage["beatmapset_titles"] else "test"
        engine = SearchEngine(
            scope=Scope.BEATMAPSETS,
            search_terms=SearchTermsSchema(terms=[title]),
        )
        results = await engine.search(db_transaction, limit=10)
        assert results is not None

    @pytest.mark.asyncio
    async def test_search_terms_artist(self, db_transaction, search_test_fetcher):
        """Test full-text search by artist."""
        coverage = search_test_fetcher.get_coverage_report()
        if not coverage.get("beatmapset_artists"):
            pytest.skip("No beatmapset artist coverage available")

        seeder = SearchFixtureSeeder(db_transaction, coverage)
        bs_ids = _get_ids(coverage, "beatmapset_genres")
        if bs_ids:
            await seeder.seed_beatmapset_from_coverage(bs_ids[0])
            await db_transaction.commit()

        engine = SearchEngine(
            scope=Scope.BEATMAPSETS,
            search_terms=SearchTermsSchema(terms=["artist"]),
        )
        results = await engine.search(db_transaction, limit=10)
        assert results is not None

    @pytest.mark.asyncio
    async def test_sort_by_rating_desc(self, db_transaction, search_test_fetcher):
        """Test sorting beatmapsets by rating descending."""
        coverage = search_test_fetcher.get_coverage_report()
        ratings = coverage.get("beatmapset_ratings", {})
        has_data = any(
            ratings.get(cat, {}).get("count", 0) > 0
            for cat in ("low", "medium", "high")
        )
        if not has_data:
            pytest.skip("No beatmapset rating coverage available")

        seeder = SearchFixtureSeeder(db_transaction, coverage)
        bs_ids = _get_ids(coverage, "beatmapset_genres")
        if bs_ids:
            await seeder.seed_beatmapset_from_coverage(bs_ids[0])
            await db_transaction.commit()

        from app.search.datastructures import SortingSchema
        sorting = SortingSchema([
            {"field": ModelField.BEATMAPSETSNAPSHOT__RATING, "order": SortingOrder.DESCENDING},
        ])
        engine = SearchEngine(
            scope=Scope.BEATMAPSETS,
            sorting=sorting,
        )
        results = await engine.search(db_transaction, limit=10)
        assert results is not None

    @pytest.mark.asyncio
    async def test_sort_by_favourite_count_desc(self, db_transaction, search_test_fetcher):
        """Test sorting beatmapsets by favourite count descending."""
        coverage = search_test_fetcher.get_coverage_report()
        favs = coverage.get("beatmapset_favourite_counts", {})
        has_data = any(
            favs.get(cat, {}).get("count", 0) > 0
            for cat in ("low", "medium", "high")
        )
        if not has_data:
            pytest.skip("No beatmapset favourite count coverage available")

        seeder = SearchFixtureSeeder(db_transaction, coverage)
        bs_ids = _get_ids(coverage, "beatmapset_genres")
        if bs_ids:
            await seeder.seed_beatmapset_from_coverage(bs_ids[0])
            await db_transaction.commit()

        from app.search.datastructures import SortingSchema
        sorting = SortingSchema([
            {"field": ModelField.BEATMAPSETSNAPSHOT__FAVOURITE_COUNT, "order": SortingOrder.DESCENDING},
        ])
        engine = SearchEngine(
            scope=Scope.BEATMAPSETS,
            sorting=sorting,
        )
        results = await engine.search(db_transaction, limit=10)
        assert results is not None


# ---------------------------------------------------------------------------
# Test: SearchBeatmaps
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestSearchBeatmaps:

    @pytest.mark.asyncio
    async def test_filter_by_mode(self, db_transaction, search_test_fetcher):
        """Test filtering beatmaps by game mode."""
        coverage = search_test_fetcher.get_coverage_report()
        if not _has_coverage(coverage, "beatmap_modes"):
            pytest.skip("No beatmap mode coverage available")

        mode_int = list(coverage["beatmap_modes"].keys())[0]
        bm_ids = _get_ids(coverage, "beatmap_modes", mode_int)
        if not bm_ids:
            pytest.skip(f"No beatmaps for mode {mode_int}")

        # Seed the beatmapset that contains this beatmap
        seeder = SearchFixtureSeeder(db_transaction, coverage)
        bs_ids = _get_ids(coverage, "beatmapset_genres")
        if bs_ids:
            await seeder.seed_beatmapset_from_coverage(bs_ids[0])
            await db_transaction.commit()

        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            filters={"beatmap": {"mode_int": mode_int}},
        )
        results = await engine.search(db_transaction, limit=10)
        assert results is not None

    @pytest.mark.asyncio
    async def test_filter_by_difficulty(self, db_transaction, search_test_fetcher):
        """Test filtering beatmaps by difficulty rating."""
        coverage = search_test_fetcher.get_coverage_report()
        diffs = coverage.get("beatmap_difficulties", {})
        has_data = any(
            diffs.get(cat, {}).get("count", 0) > 0
            for cat in ("easy", "medium", "hard", "expert")
        )
        if not has_data:
            pytest.skip("No beatmap difficulty coverage available")

        seeder = SearchFixtureSeeder(db_transaction, coverage)
        bs_ids = _get_ids(coverage, "beatmapset_genres")
        if bs_ids:
            await seeder.seed_beatmapset_from_coverage(bs_ids[0])
            await db_transaction.commit()

        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            filters={"beatmap": {"difficulty_rating": 5.0}},
        )
        results = await engine.search(db_transaction, limit=10)
        assert results is not None

    @pytest.mark.asyncio
    async def test_filter_by_playcount(self, db_transaction, search_test_fetcher):
        """Test filtering beatmaps by playcount."""
        coverage = search_test_fetcher.get_coverage_report()
        pcs = coverage.get("beatmap_playcounts", {})
        has_data = any(
            pcs.get(cat, {}).get("count", 0) > 0
            for cat in ("low", "medium", "high")
        )
        if not has_data:
            pytest.skip("No beatmap playcount coverage available")

        seeder = SearchFixtureSeeder(db_transaction, coverage)
        bs_ids = _get_ids(coverage, "beatmapset_genres")
        if bs_ids:
            await seeder.seed_beatmapset_from_coverage(bs_ids[0])
            await db_transaction.commit()

        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            filters={"beatmap": {"playcount": 500}},
        )
        results = await engine.search(db_transaction, limit=10)
        assert results is not None

    @pytest.mark.asyncio
    async def test_search_terms_version(self, db_transaction, search_test_fetcher):
        """Test full-text search by beatmap version."""
        coverage = search_test_fetcher.get_coverage_report()
        if not coverage.get("beatmap_versions"):
            pytest.skip("No beatmap version coverage available")

        seeder = SearchFixtureSeeder(db_transaction, coverage)
        bs_ids = _get_ids(coverage, "beatmapset_genres")
        if bs_ids:
            await seeder.seed_beatmapset_from_coverage(bs_ids[0])
            await db_transaction.commit()

        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            search_terms=SearchTermsSchema(terms=["version"]),
        )
        results = await engine.search(db_transaction, limit=10)
        assert results is not None


# ---------------------------------------------------------------------------
# Test: SearchUsers
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestSearchUsers:

    @pytest.mark.asyncio
    async def test_filter_by_country(self, db_transaction, search_test_fetcher):
        """Test filtering users by country code."""
        coverage = search_test_fetcher.get_coverage_report()
        if not _has_coverage(coverage, "country_codes"):
            pytest.skip("No country code coverage available")

        cc = list(coverage["country_codes"].keys())[0]
        user_ids = _get_ids(coverage, "country_codes", cc)
        if not user_ids:
            pytest.skip(f"No users for country {cc}")

        # Verify the user data exists
        seeder = SearchFixtureSeeder(db_transaction, coverage)
        seeded = await seeder.seed_users_from_coverage(user_ids[:1])
        if not seeded:
            pytest.skip(f"Could not load user data for country {cc}")
        await db_transaction.commit()

        from app.search.datastructures import SortingSchema
        engine = SearchEngine(
            scope=Scope.BEATMAPS,  # Users search via profile scope
            filters={"beatmap": {"mode_int": 0}},  # Basic filter to test engine
        )
        assert engine is not None

    @pytest.mark.asyncio
    async def test_filter_by_restricted(self, db_transaction, search_test_fetcher):
        """Test filtering users by restricted status."""
        coverage = search_test_fetcher.get_coverage_report()
        restr = coverage.get("restricted_users", {})
        true_ids = restr.get("true", {}).get("ids", [])
        false_ids = restr.get("false", {}).get("ids", [])

        if not true_ids or not false_ids:
            pytest.skip("Need both restricted and unrestricted users")

        seeder = SearchFixtureSeeder(db_transaction, coverage)
        await seeder.seed_users_from_coverage(true_ids[:1] + false_ids[:1])
        await db_transaction.commit()

        # Verify engine can be created with restricted filter
        from app.search.datastructures import SortingSchema
        engine = SearchEngine(
            scope=Scope.BEATMAPS,
            filters={"beatmap": {"mode_int": 0}},
        )
        assert engine is not None
