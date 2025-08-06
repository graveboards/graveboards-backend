from typing import Iterable, Any

from sqlalchemy.sql import select, desc
from sqlalchemy.sql.selectable import Select
from sqlalchemy.orm.strategy_options import selectinload, joinedload, noload, defer, Load
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import *
from app.utils import clamp
from .decorators import session_manager
from .types import LoadingStrategy, LoadingOptions, LoadingOptionsConfig

QUERY_MIN_LIMIT = 1
QUERY_MAX_LIMIT = 100
QUERY_DEFAULT_LIMIT = 50


class _R:
    @staticmethod
    async def _get_instance(
            model_class: ModelClass,
            session: AsyncSession,
            **kwargs
    ) -> BaseType:
        select_stmt = _R._construct_stmt(model_class, **kwargs)

        return await session.scalar(select_stmt)

    @staticmethod
    async def _get_instances(
            model_class: ModelClass,
            session: AsyncSession,
            _limit: int = QUERY_DEFAULT_LIMIT,
            _offset: int = 0,
            **kwargs
    ) -> list[BaseType]:
        select_stmt = _R._construct_stmt(model_class, **kwargs)
        select_stmt = select_stmt.limit(clamp(_limit, QUERY_MIN_LIMIT, QUERY_MAX_LIMIT)).offset(_offset)

        return list((await session.scalars(select_stmt)).all())

    @staticmethod
    def _construct_stmt(
            model_class: ModelClass,
            _where: Any | Iterable[Any] = None,
            _reversed: bool = False,
            _loading_options: LoadingOptions = None,
            _eager_loads: dict[str, LoadingStrategy] = None,  # Deprecated
            _auto_eager_loads: Iterable[str] = None,  # Deprecated
            _exclude: Iterable[str] = None,
            _exclude_lazy: bool = False,
            **kwargs
    ) -> Select:
        if _eager_loads or _auto_eager_loads:
            raise DeprecationWarning("_eager_loads and _auto_eager_loads are deprecated, use _loading_options instead")
        if _loading_options and (_eager_loads or _auto_eager_loads):
            raise ValueError("_loading_options are mutually exclusive to _eager_loads and _auto_eager_loads")
        if _eager_loads and _auto_eager_loads:
            raise ValueError("_eager_loads and _auto_eager_loads are mutually exclusive")

        select_stmt = select(model_class.value).filter_by(**kwargs)

        if _where is not None:
            if not isinstance(_where, Iterable):
                _where = (_where,)

            select_stmt = select_stmt.where(*_where)

        if _reversed:
            select_stmt = _R._apply_reversed(select_stmt, model_class)

        if _loading_options:
            select_stmt = _R._apply_loading_options(select_stmt, model_class, _loading_options)

        if _eager_loads:
            select_stmt = _R._apply_eager_loads(select_stmt, model_class, _eager_loads)

        if _auto_eager_loads:
            select_stmt = _R._apply_auto_eager_loads(select_stmt, model_class, _auto_eager_loads)

        if _exclude:
            select_stmt = _R._apply_exclude(select_stmt, model_class, _exclude)

        if _exclude_lazy:
            select_stmt = _R._apply_exclude_lazy(select_stmt, model_class)

        return select_stmt

    @staticmethod
    def _apply_reversed(select_stmt: Select, model_class: ModelClass) -> Select:
        return select_stmt.order_by(desc(model_class.mapper.primary_key[0]))

    @staticmethod
    def _apply_eager_loads(select_stmt: Select, model_class: ModelClass, eager_loads: dict[str, LoadingStrategy]) -> Select:
        load_options = []

        for attr_name, strategy in eager_loads.items():
            if attr_name in model_class.mapper.relationships:
                attr = model_class.mapper.attrs[attr_name]

                if strategy == "joinedload":
                    load_options.append(joinedload(attr))
                elif strategy == "selectinload":
                    load_options.append(selectinload(attr))
                else:
                    raise ValueError(f"Unsupported loading strategy: {strategy}")
            else:
                raise ValueError(f"{attr_name} is not a valid relationship in {model_class.value}")

        return select_stmt.options(*load_options)

    @staticmethod
    def _apply_auto_eager_loads(select_stmt: Select, model_class: ModelClass, relationships: Iterable[str]) -> Select:
        load_options = []

        for attr_name in relationships:
            if attr_name in model_class.mapper.relationships:
                attr = model_class.mapper.attrs[attr_name]
                is_collection = model_class.mapper.relationships[attr_name].uselist

                if is_collection:
                    load_options.append(selectinload(attr))
                else:
                    load_options.append(joinedload(attr))
            else:
                raise ValueError(f"{attr_name} is not a valid relationship in {model_class.value}")

        return select_stmt.options(*load_options)

    @staticmethod
    def _apply_loading_options(select_stmt: Select, model_class: ModelClass, loading_options: LoadingOptions) -> Select:
        def parse_node(attr_name: str, config: LoadingOptionsConfig, parent_model_class: ModelClass) -> Load:
            if attr_name not in parent_model_class.mapper.relationships:
                raise ValueError(f"{attr_name} is not a valid relationship in {parent_model_class.value}")

            attr = parent_model_class.mapper.attrs[attr_name]
            rel_info = parent_model_class.mapper.relationships[attr_name]
            target_model_class = ModelClass(rel_info.mapper.class_)

            if config is True:
                strategy = "selectinload" if rel_info.uselist else "joinedload"
                children = None
            elif config is False:
                strategy = "noload"
                children = None
            elif isinstance(config, str):
                strategy = config
                children = None
            elif isinstance(config, dict):
                strategy = config.get("strategy")
                children = config.get("options")

                if strategy is None:
                    strategy = "selectinload" if rel_info.uselist else "joinedload"
            else:
                raise ValueError(f"Invalid config for relationship '{attr_name}': {config}")

            if strategy == "joinedload":
                loader = joinedload(attr)
            elif strategy == "selectinload":
                loader = selectinload(attr)
            elif strategy == "noload":
                loader = noload(attr)
            else:
                raise ValueError(f"Unsupported loading strategy: {strategy}")

            if children and strategy != "noload":
                for child_attr, child_config in children.items():
                    loader = loader.options(parse_node(child_attr, child_config, target_model_class))

            return loader

        load_options = [parse_node(attr, config, model_class) for attr, config in loading_options.items()]
        return select_stmt.options(*load_options)

    @staticmethod
    def _apply_exclude(select_stmt: Select, model_class: ModelClass, exclude: Iterable[str]) -> Select:
        load_options = []

        for attr_name in exclude:
            if attr_name in model_class.mapper.columns:
                attr = model_class.mapper.attrs[attr_name]
                load_options.append(defer(attr))
            elif attr_name in model_class.mapper.relationships:
                attr = model_class.mapper.attrs[attr_name]
                load_options.append(noload(attr))
            else:
                raise ValueError(f"{attr_name} is not a valid column nor relationship in {model_class.value}")

        return select_stmt.options(*load_options)


    @staticmethod
    def _apply_exclude_lazy(select_stmt: Select, model_class: ModelClass) -> Select:
        noload_relationships = [
            noload(attr)
            for attr in model_class.mapper.relationships
            if attr.lazy is True or attr.lazy in {"select", "dynamic", "raise_on_sql"}
        ]

        return select_stmt.options(*noload_relationships)


class R(_R):
    @session_manager
    async def get_user(self, session: AsyncSession = None, **kwargs) -> User | None:
        return await self._get_instance(ModelClass.USER, session, **kwargs)

    @session_manager
    async def get_users(self, session: AsyncSession = None, **kwargs) -> list[User]:
        return await self._get_instances(ModelClass.USER, session, **kwargs)

    @session_manager
    async def get_role(self, session: AsyncSession = None, **kwargs) -> Role | None:
        return await self._get_instance(ModelClass.ROLE, session, **kwargs)

    @session_manager
    async def get_roles(self, session: AsyncSession = None, **kwargs) -> list[Role]:
        return await self._get_instances(ModelClass.ROLE, session, **kwargs)

    @session_manager
    async def get_profile(self, session: AsyncSession = None, **kwargs) -> Profile | None:
        return await self._get_instance(ModelClass.PROFILE, session, **kwargs)

    @session_manager
    async def get_profiles(self, session: AsyncSession = None, **kwargs) -> list[Profile]:
        return await self._get_instances(ModelClass.PROFILE, session, **kwargs)

    @session_manager
    async def get_api_key(self, session: AsyncSession = None, **kwargs) -> ApiKey | None:
        return await self._get_instance(ModelClass.API_KEY, session, **kwargs)

    @session_manager
    async def get_api_keys(self, session: AsyncSession = None, **kwargs) -> list[ApiKey]:
        return await self._get_instances(ModelClass.API_KEY, session, **kwargs)

    @session_manager
    async def get_oauth_token(self, session: AsyncSession = None, **kwargs) -> OAuthToken | None:
        return await self._get_instance(ModelClass.OAUTH_TOKEN, session, **kwargs)

    @session_manager
    async def get_oauth_tokens(self, session: AsyncSession = None, **kwargs) -> list[OAuthToken]:
        return await self._get_instances(ModelClass.OAUTH_TOKEN, session, **kwargs)

    @session_manager
    async def get_jwt(self, session: AsyncSession = None, **kwargs) -> JWT | None:
        return await self._get_instance(ModelClass.JWT, session, **kwargs)

    @session_manager
    async def get_jwts(self, session: AsyncSession = None, **kwargs) -> list[JWT]:
        return await self._get_instances(ModelClass.JWT, session, **kwargs)

    @session_manager
    async def get_score_fetcher_task(self, session: AsyncSession = None, **kwargs) -> ScoreFetcherTask | None:
        return await self._get_instance(ModelClass.SCORE_FETCHER_TASK, session, **kwargs)

    @session_manager
    async def get_score_fetcher_tasks(self, session: AsyncSession = None, **kwargs) -> list[ScoreFetcherTask]:
        return await self._get_instances(ModelClass.SCORE_FETCHER_TASK, session, **kwargs)

    @session_manager
    async def get_profile_fetcher_task(self, session: AsyncSession = None, **kwargs) -> ProfileFetcherTask | None:
        return await self._get_instance(ModelClass.PROFILE_FETCHER_TASK, session, **kwargs)

    @session_manager
    async def get_profile_fetcher_tasks(self, session: AsyncSession = None, **kwargs) -> list[ProfileFetcherTask]:
        return await self._get_instances(ModelClass.PROFILE_FETCHER_TASK, session, **kwargs)

    @session_manager
    async def get_beatmap(self, session: AsyncSession = None, **kwargs) -> Beatmap | None:
        return await self._get_instance(ModelClass.BEATMAP, session, **kwargs)

    @session_manager
    async def get_beatmaps(self, session: AsyncSession = None, **kwargs) -> list[Beatmap]:
        return await self._get_instances(ModelClass.BEATMAP, session, **kwargs)

    @session_manager
    async def get_beatmap_snapshot(self, session: AsyncSession = None, **kwargs) -> BeatmapSnapshot | None:
        return await self._get_instance(ModelClass.BEATMAP_SNAPSHOT, session, **kwargs)

    @session_manager
    async def get_beatmap_snapshots(self, session: AsyncSession = None, **kwargs) -> list[BeatmapSnapshot]:
        return await self._get_instances(ModelClass.BEATMAP_SNAPSHOT, session, **kwargs)

    @session_manager
    async def get_beatmapset(self, session: AsyncSession = None, **kwargs) -> Beatmapset | None:
        return await self._get_instance(ModelClass.BEATMAPSET, session, **kwargs)

    @session_manager
    async def get_beatmapsets(self, session: AsyncSession = None, **kwargs) -> list[Beatmapset]:
        return await self._get_instances(ModelClass.BEATMAPSET, session, **kwargs)

    @session_manager
    async def get_beatmapset_snapshot(self, session: AsyncSession = None, **kwargs) -> BeatmapsetSnapshot | None:
        return await self._get_instance(ModelClass.BEATMAPSET_SNAPSHOT, session, **kwargs)

    @session_manager
    async def get_beatmapset_snapshots(self, session: AsyncSession = None, **kwargs) -> list[BeatmapsetSnapshot]:
        return await self._get_instances(ModelClass.BEATMAPSET_SNAPSHOT, session, **kwargs)

    @session_manager
    async def get_beatmapset_listing(self, session: AsyncSession = None, **kwargs) -> BeatmapsetListing | None:
        return await self._get_instance(ModelClass.BEATMAPSET_LISTING, session, **kwargs)

    @session_manager
    async def get_beatmapset_listings(self, session: AsyncSession = None, **kwargs) -> list[BeatmapsetListing]:
        return await self._get_instances(ModelClass.BEATMAPSET_LISTING, session, **kwargs)

    @session_manager
    async def get_leaderboard(self, session: AsyncSession = None, **kwargs) -> Leaderboard | None:
        return await self._get_instance(ModelClass.LEADERBOARD, session, **kwargs)

    @session_manager
    async def get_leaderboards(self, session: AsyncSession = None, **kwargs) -> list[Leaderboard]:
        return await self._get_instances(ModelClass.LEADERBOARD, session, **kwargs)

    @session_manager
    async def get_score(self, session: AsyncSession = None, **kwargs) -> Score | None:
        return await self._get_instance(ModelClass.SCORE, session, **kwargs)

    @session_manager
    async def get_scores(self, session: AsyncSession = None, **kwargs) -> list[Score]:
        return await self._get_instances(ModelClass.SCORE, session, **kwargs)

    @session_manager
    async def get_queue(self, session: AsyncSession = None, **kwargs) -> Queue | None:
        return await self._get_instance(ModelClass.QUEUE, session, **kwargs)

    @session_manager
    async def get_queues(self, session: AsyncSession = None, **kwargs) -> list[Queue]:
        return await self._get_instances(ModelClass.QUEUE, session, **kwargs)

    @session_manager
    async def get_queue_listing(self, session: AsyncSession = None, **kwargs) -> QueueListing | None:
        return await self._get_instance(ModelClass.QUEUE_LISTING, session, **kwargs)

    @session_manager
    async def get_queue_listings(self, session: AsyncSession = None, **kwargs) -> list[QueueListing]:
        return await self._get_instances(ModelClass.QUEUE_LISTING, session, **kwargs)

    @session_manager
    async def get_request(self, session: AsyncSession = None, **kwargs) -> Request | None:
        return await self._get_instance(ModelClass.REQUEST, session, **kwargs)

    @session_manager
    async def get_requests(self, session: AsyncSession = None, **kwargs) -> list[Request]:
        return await self._get_instances(ModelClass.REQUEST, session, **kwargs)

    @session_manager
    async def get_request_listing(self, session: AsyncSession = None, **kwargs) -> RequestListing | None:
        return await self._get_instance(ModelClass.REQUEST_LISTING, session, **kwargs)

    @session_manager
    async def get_request_listings(self, session: AsyncSession = None, **kwargs) -> list[RequestListing]:
        return await self._get_instances(ModelClass.REQUEST_LISTING, session, **kwargs)

    @session_manager
    async def get_beatmapset_tag(self, session: AsyncSession = None, **kwargs) -> BeatmapsetTag | None:
        return await self._get_instance(ModelClass.BEATMAPSET_TAG, session, **kwargs)

    @session_manager
    async def get_beatmapset_tags(self, session: AsyncSession = None, **kwargs) -> list[BeatmapsetTag]:
        return await self._get_instances(ModelClass.BEATMAPSET_TAG, session, **kwargs)

    @session_manager
    async def get_beatmap_tag(self, session: AsyncSession = None, **kwargs) -> BeatmapTag | None:
        return await self._get_instance(ModelClass.BEATMAP_TAG, session, **kwargs)

    @session_manager
    async def get_beatmap_tags(self, session: AsyncSession = None, **kwargs) -> list[BeatmapTag]:
        return await self._get_instances(ModelClass.BEATMAP_TAG, session, **kwargs)
