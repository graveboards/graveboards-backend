from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import *
from .decorators import session_manager, ensure_required


class _C:
    @staticmethod
    @ensure_required
    async def _add_instance(model_class: ModelClass, session: AsyncSession, **kwargs) -> BaseType:
        instance = model_class.value(**kwargs)

        session.add(instance)
        await session.commit()
        await session.refresh(instance)

        return instance


class C(_C):
    @session_manager
    async def add_user(self, session: AsyncSession = None, **kwargs) -> User:
        return await self._add_instance(ModelClass.USER, session, **kwargs)

    @session_manager
    async def add_role(self, session: AsyncSession = None, **kwargs) -> Role:
        return await self._add_instance(ModelClass.ROLE, session, **kwargs)

    @session_manager
    async def add_profile(self, session: AsyncSession = None, **kwargs) -> Profile:
        return await self._add_instance(ModelClass.PROFILE, session, **kwargs)

    @session_manager
    async def add_api_key(self, session: AsyncSession = None, **kwargs) -> ApiKey:
        return await self._add_instance(ModelClass.API_KEY, session, **kwargs)

    @session_manager
    async def add_oauth_token(self, session: AsyncSession = None, **kwargs) -> OAuthToken:
        return await self._add_instance(ModelClass.OAUTH_TOKEN, session, **kwargs)

    @session_manager
    async def add_jwt(self, session: AsyncSession = None, **kwargs) -> JWT:
        return await self._add_instance(ModelClass.JWT, session, **kwargs)

    @session_manager
    async def add_score_fetcher_task(self, session: AsyncSession = None, **kwargs) -> ScoreFetcherTask:
        return await self._add_instance(ModelClass.SCORE_FETCHER_TASK, session, **kwargs)

    @session_manager
    async def add_profile_fetcher_task(self, session: AsyncSession = None, **kwargs) -> ProfileFetcherTask:
        return await self._add_instance(ModelClass.PROFILE_FETCHER_TASK, session, **kwargs)

    @session_manager
    async def add_beatmap(self, session: AsyncSession = None, **kwargs) -> Beatmap:
        return await self._add_instance(ModelClass.BEATMAP, session, **kwargs)

    @session_manager
    async def add_beatmap_snapshot(self, session: AsyncSession = None, **kwargs) -> BeatmapSnapshot:
        return await self._add_instance(ModelClass.BEATMAP_SNAPSHOT, session, **kwargs)

    @session_manager
    async def add_beatmapset(self, session: AsyncSession = None, **kwargs) -> Beatmapset:
        return await self._add_instance(ModelClass.BEATMAPSET, session, **kwargs)

    @session_manager
    async def add_beatmapset_snapshot(self, session: AsyncSession = None, **kwargs) -> BeatmapsetSnapshot:
        return await self._add_instance(ModelClass.BEATMAPSET_SNAPSHOT, session, **kwargs)

    @session_manager
    async def add_beatmapset_listing(self, session: AsyncSession = None, **kwargs) -> BeatmapsetListing:
        return await self._add_instance(ModelClass.BEATMAPSET_LISTING, session, **kwargs)

    @session_manager
    async def add_leaderboard(self, session: AsyncSession = None, **kwargs) -> Leaderboard:
        return await self._add_instance(ModelClass.LEADERBOARD, session, **kwargs)

    @session_manager
    async def add_score(self, session: AsyncSession = None, **kwargs) -> Score:
        return await self._add_instance(ModelClass.SCORE, session, **kwargs)

    @session_manager
    async def add_queue(self, session: AsyncSession = None, **kwargs) -> Queue:
        return await self._add_instance(ModelClass.QUEUE, session, **kwargs)

    @session_manager
    async def add_request(self, session: AsyncSession = None, **kwargs) -> Request:
        return await self._add_instance(ModelClass.REQUEST, session, **kwargs)

    @session_manager
    async def add_beatmapset_tag(self, session: AsyncSession = None, **kwargs) -> BeatmapsetTag:
        return await self._add_instance(ModelClass.BEATMAPSET_TAG, session, **kwargs)

    @session_manager
    async def add_beatmap_tag(self, session: AsyncSession = None, **kwargs) -> BeatmapTag:
        return await self._add_instance(ModelClass.BEATMAP_TAG, session, **kwargs)
