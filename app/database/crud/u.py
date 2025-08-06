from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import *
from .decorators import session_manager


class _U:
    @staticmethod
    async def _update_instance(model_class: ModelClass, session: AsyncSession, primary_key: int, **kwargs) -> BaseType:
        instance = await session.get(model_class.value, primary_key)

        if instance is None:
            raise ValueError(f"There is no {model_class.value.__name__} with the primary key '{primary_key}'")

        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
            else:
                raise ValueError(f"{model_class.value.__name__} has no attribute '{key}'")

        await session.commit()
        await session.refresh(instance)

        return instance


class U(_U):
    @session_manager
    async def update_user(self, primary_key: int, session: AsyncSession = None, **kwargs) -> User:
        return await self._update_instance(ModelClass.USER, session, primary_key, **kwargs)

    @session_manager
    async def update_role(self, primary_key: int, session: AsyncSession = None, **kwargs) -> Role:
        return await self._update_instance(ModelClass.ROLE, session, primary_key, **kwargs)

    @session_manager
    async def update_profile(self, primary_key: int, session: AsyncSession = None, **kwargs) -> Profile:
        return await self._update_instance(ModelClass.PROFILE, session, primary_key, **kwargs)

    @session_manager
    async def update_api_key(self, primary_key: int, session: AsyncSession = None, **kwargs) -> ApiKey:
        return await self._update_instance(ModelClass.API_KEY, session, primary_key, **kwargs)

    @session_manager
    async def update_oauth_token(self, primary_key: int, session: AsyncSession = None, **kwargs) -> OAuthToken:
        return await self._update_instance(ModelClass.OAUTH_TOKEN, session, primary_key, **kwargs)

    @session_manager
    async def update_jwt(self, primary_key: int, session: AsyncSession = None, **kwargs) -> JWT:
        return await self._update_instance(ModelClass.JWT, session, primary_key, **kwargs)

    @session_manager
    async def update_score_fetcher_task(self, primary_key: int, session: AsyncSession = None, **kwargs) -> ScoreFetcherTask:
        return await self._update_instance(ModelClass.SCORE_FETCHER_TASK, session, primary_key, **kwargs)

    @session_manager
    async def update_profile_fetcher_task(self, primary_key: int, session: AsyncSession = None, **kwargs) -> ProfileFetcherTask:
        return await self._update_instance(ModelClass.PROFILE_FETCHER_TASK, session, primary_key, **kwargs)

    @session_manager
    async def update_beatmap(self, primary_key: int, session: AsyncSession = None, **kwargs) -> Beatmap:
        return await self._update_instance(ModelClass.BEATMAP, session, primary_key, **kwargs)

    @session_manager
    async def update_beatmap_snapshot(self, primary_key: int, session: AsyncSession = None, **kwargs) -> BeatmapSnapshot:
        return await self._update_instance(ModelClass.BEATMAP_SNAPSHOT, session, primary_key, **kwargs)

    @session_manager
    async def update_beatmapset(self, primary_key: int, session: AsyncSession = None, **kwargs) -> Beatmapset:
        return await self._update_instance(ModelClass.BEATMAPSET, session, primary_key, **kwargs)

    @session_manager
    async def update_beatmapset_snapshot(self, primary_key: int, session: AsyncSession = None, **kwargs) -> BeatmapsetSnapshot:
        return await self._update_instance(ModelClass.BEATMAPSET_SNAPSHOT, session, primary_key, **kwargs)

    @session_manager
    async def update_beatmapset_listing(self, primary_key: int, session: AsyncSession = None, **kwargs) -> BeatmapsetListing:
        return await self._update_instance(ModelClass.BEATMAPSET_LISTING, session, primary_key, **kwargs)

    @session_manager
    async def update_leaderboard(self, primary_key: int, session: AsyncSession = None, **kwargs) -> Leaderboard:
        return await self._update_instance(ModelClass.LEADERBOARD, session, primary_key, **kwargs)

    @session_manager
    async def update_score(self, primary_key: int, session: AsyncSession = None, **kwargs) -> Score:
        return await self._update_instance(ModelClass.SCORE, session, primary_key, **kwargs)

    @session_manager
    async def update_queue(self, primary_key: int, session: AsyncSession = None, **kwargs) -> Queue:
        return await self._update_instance(ModelClass.QUEUE, session, primary_key, **kwargs)

    @session_manager
    async def update_request(self, primary_key: int, session: AsyncSession = None, **kwargs) -> Request:
        return await self._update_instance(ModelClass.REQUEST, session, primary_key, **kwargs)

    @session_manager
    async def update_beatmapset_tag(self, primary_key: int, session: AsyncSession = None, **kwargs) -> BeatmapsetTag:
        return await self._update_instance(ModelClass.BEATMAPSET_TAG, session, primary_key, **kwargs)

    @session_manager
    async def update_beatmap_tag(self, primary_key: int, session: AsyncSession = None, **kwargs) -> BeatmapTag:
        return await self._update_instance(ModelClass.BEATMAP_TAG, session, primary_key, **kwargs)
