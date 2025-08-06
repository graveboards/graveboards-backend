from sqlalchemy.sql import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import *
from .decorators import session_manager


class _D:
    @staticmethod
    async def _delete_instance(model_class: ModelClass, session: AsyncSession, **kwargs) -> bool:
        select_stmt = select(model_class.value).filter_by(**kwargs).limit(1)

        instance = session.scalar(select_stmt)

        if instance is None:
            return False

        await session.delete(instance)
        await session.commit()

        return True

    @staticmethod
    async def _delete_instances(model_class: ModelClass, session: AsyncSession, **kwargs) -> int:
        delete_stmt = delete(model_class.value).filter_by(**kwargs)

        result = await session.execute(delete_stmt)
        await session.commit()

        return await result.rowcount


class D(_D):
    @session_manager
    async def delete_user(self, session: AsyncSession = None, **kwargs) -> bool:
        return await self._delete_instance(ModelClass.USER, session, **kwargs)

    @session_manager
    async def delete_users(self, session: AsyncSession = None, **kwargs) -> int:
        return await self._delete_instances(ModelClass.USER, session, **kwargs)

    @session_manager
    async def delete_role(self, session: AsyncSession = None, **kwargs) -> bool:
        return await self._delete_instance(ModelClass.ROLE, session, **kwargs)

    @session_manager
    async def delete_roles(self, session: AsyncSession = None, **kwargs) -> int:
        return await self._delete_instances(ModelClass.ROLE, session, **kwargs)

    @session_manager
    async def delete_profile(self, session: AsyncSession = None, **kwargs) -> bool:
        return await self._delete_instance(ModelClass.PROFILE, session, **kwargs)

    @session_manager
    async def delete_profiles(self, session: AsyncSession = None, **kwargs) -> int:
        return await self._delete_instances(ModelClass.PROFILE, session, **kwargs)

    @session_manager
    async def delete_api_key(self, session: AsyncSession = None, **kwargs) -> bool:
        return await self._delete_instance(ModelClass.API_KEY, session, **kwargs)

    @session_manager
    async def delete_api_keys(self, session: AsyncSession = None, **kwargs) -> int:
        return await self._delete_instances(ModelClass.API_KEY, session, **kwargs)

    @session_manager
    async def delete_oauth_token(self, session: AsyncSession = None, **kwargs) -> bool:
        return await self._delete_instance(ModelClass.OAUTH_TOKEN, session, **kwargs)

    @session_manager
    async def delete_oauth_tokens(self, session: AsyncSession = None, **kwargs) -> int:
        return await self._delete_instances(ModelClass.OAUTH_TOKEN, session, **kwargs)

    @session_manager
    async def delete_jwt(self, session: AsyncSession = None, **kwargs) -> bool:
        return await self._delete_instance(ModelClass.JWT, session, **kwargs)

    @session_manager
    async def delete_jwts(self, session: AsyncSession = None, **kwargs) -> int:
        return await self._delete_instances(ModelClass.JWT, session, **kwargs)

    @session_manager
    async def delete_score_fetcher_task(self, session: AsyncSession = None, **kwargs) -> bool:
        return await self._delete_instance(ModelClass.SCORE_FETCHER_TASK, session, **kwargs)

    @session_manager
    async def delete_score_fetcher_tasks(self, session: AsyncSession = None, **kwargs) -> int:
        return await self._delete_instances(ModelClass.SCORE_FETCHER_TASK, session, **kwargs)

    @session_manager
    async def delete_profile_fetcher_task(self, session: AsyncSession = None, **kwargs) -> bool:
        return await self._delete_instance(ModelClass.PROFILE_FETCHER_TASK, session, **kwargs)

    @session_manager
    async def delete_profile_fetcher_tasks(self, session: AsyncSession = None, **kwargs) -> int:
        return await self._delete_instances(ModelClass.PROFILE_FETCHER_TASK, session, **kwargs)

    @session_manager
    async def delete_beatmap(self, session: AsyncSession = None, **kwargs) -> bool:
        return await self._delete_instance(ModelClass.BEATMAP, session, **kwargs)

    @session_manager
    async def delete_beatmaps(self, session: AsyncSession = None, **kwargs) -> int:
        return await self._delete_instances(ModelClass.BEATMAP, session, **kwargs)

    @session_manager
    async def delete_beatmap_snapshot(self, session: AsyncSession = None, **kwargs) -> bool:
        return await self._delete_instance(ModelClass.BEATMAP_SNAPSHOT, session, **kwargs)

    @session_manager
    async def delete_beatmap_snapshots(self, session: AsyncSession = None, **kwargs) -> int:
        return await self._delete_instances(ModelClass.BEATMAP_SNAPSHOT, session, **kwargs)

    @session_manager
    async def delete_beatmapset(self, session: AsyncSession = None, **kwargs) -> bool:
        return await self._delete_instance(ModelClass.BEATMAPSET, session, **kwargs)

    @session_manager
    async def delete_beatmapsets(self, session: AsyncSession = None, **kwargs) -> int:
        return await self._delete_instances(ModelClass.BEATMAPSET, session, **kwargs)

    @session_manager
    async def delete_beatmapset_snapshot(self, session: AsyncSession = None, **kwargs) -> bool:
        return await self._delete_instance(ModelClass.BEATMAPSET_SNAPSHOT, session, **kwargs)

    @session_manager
    async def delete_beatmapset_snapshots(self, session: AsyncSession = None, **kwargs) -> int:
        return await self._delete_instances(ModelClass.BEATMAPSET_SNAPSHOT, session, **kwargs)

    @session_manager
    async def delete_beatmapset_listing(self, session: AsyncSession = None, **kwargs) -> bool:
        return await self._delete_instance(ModelClass.BEATMAPSET_LISTING, session, **kwargs)

    @session_manager
    async def delete_beatmapset_listings(self, session: AsyncSession = None, **kwargs) -> int:
        return await self._delete_instances(ModelClass.BEATMAPSET_LISTING, session, **kwargs)

    @session_manager
    async def delete_leaderboard(self, session: AsyncSession = None, **kwargs) -> bool:
        return await self._delete_instance(ModelClass.LEADERBOARD, session, **kwargs)

    @session_manager
    async def delete_leaderboards(self, session: AsyncSession = None, **kwargs) -> int:
        return await self._delete_instances(ModelClass.LEADERBOARD, session, **kwargs)

    @session_manager
    async def delete_score(self, session: AsyncSession = None, **kwargs) -> bool:
        return await self._delete_instance(ModelClass.SCORE, session, **kwargs)

    @session_manager
    async def delete_scores(self, session: AsyncSession = None, **kwargs) -> int:
        return await self._delete_instances(ModelClass.SCORE, session, **kwargs)

    @session_manager
    async def delete_queue(self, session: AsyncSession = None, **kwargs) -> bool:
        return await self._delete_instance(ModelClass.QUEUE, session, **kwargs)

    @session_manager
    async def delete_queues(self, session: AsyncSession = None, **kwargs) -> int:
        return await self._delete_instances(ModelClass.QUEUE, session, **kwargs)

    @session_manager
    async def delete_request(self, session: AsyncSession = None, **kwargs) -> bool:
        return await self._delete_instance(ModelClass.REQUEST, session, **kwargs)

    @session_manager
    async def delete_requests(self, session: AsyncSession = None, **kwargs) -> int:
        return await self._delete_instances(ModelClass.REQUEST, session, **kwargs)

    @session_manager
    async def delete_tag(self, session: AsyncSession = None, **kwargs) -> bool:
        return await self._delete_instance(ModelClass.BEATMAPSET_TAG, session, **kwargs)

    @session_manager
    async def delete_tags(self, session: AsyncSession = None, **kwargs) -> int:
        return await self._delete_instances(ModelClass.BEATMAPSET_TAG, session, **kwargs)
