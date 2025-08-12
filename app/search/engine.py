from typing import Union, Optional, Any, Sequence, Generator

from sqlalchemy.sql import and_, select
from sqlalchemy.sql.selectable import CTE
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.elements import BinaryExpression, literal_column
from sqlalchemy.orm.strategy_options import joinedload, noload, selectinload
from sqlalchemy.engine.result import MappingResult
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.selectable import Select

from app.database.models import (
    ModelClass,
    BeatmapListing,
    BeatmapsetListing,
    BeatmapsetSnapshot,
    BeatmapSnapshot,
    Queue,
    Request,
    beatmap_snapshot_beatmapset_snapshot_association
)
from app.database.schemas import (
    BeatmapListingSchema,
    BeatmapsetListingSchema,
    QueueSchema,
    RequestSchema
)
from app.database.ctes.search_terms_scored import (
    search_terms_scored_ctes_factory,
    aggregated_child_scores_to_parent_cte_factory
)
from app.database.ctes.search_terms_filtered import search_terms_filtered_cte_factory
from app.database.ctes.bms_ss.sorting import bms_ss_sorting_cte_factory
from app.database.ctes.bms_ss.filtering import bms_ss_filtering_cte_factory
from app.database.ctes.bm_ss.sorting import bm_ss_sorting_cte_factory
from app.database.ctes.bm_ss.filtering import bm_ss_filtering_cte_factory
from app.database.ctes.profile.sorting import profile_sorting_cte_factory
from app.database.ctes.profile.filtering import profile_filtering_cte_factory
from app.database.ctes.request.sorting import request_sorting_cte_factory
from app.database.ctes.request.filtering import request_filtering_cte_factory
from app.database.ctes.queue.sorting import queue_sorting_cte_factory
from app.database.ctes.queue.filtering import queue_filtering_cte_factory
from app.database.utils import get_filter_condition
from app.search.datastructures import ConditionValue, SearchTermsSchema, SortingSchema, FiltersSchema
from app.search.enums import Scope, SearchableFieldCategory, FilterOperator, ModelField, CATEGORY_NAMES

DEFAULT_LIMIT = 50
DEFAULT_OFFSET = 0
ResultsType = Union[Sequence[BeatmapListing], Sequence[BeatmapsetListing], ..., Sequence[Queue], Sequence[Request]]

SCOPE_MODEL_MAPPING = {
    Scope.BEATMAPS: ModelClass.BEATMAP_LISTING,
    Scope.BEATMAPSETS: ModelClass.BEATMAPSET_LISTING,
    Scope.SCORES: ...,
    Scope.QUEUES: ModelClass.QUEUE,
    Scope.REQUESTS: ModelClass.REQUEST
}

SCOPE_SCHEMA_MAPPING = {
    Scope.BEATMAPS: BeatmapListingSchema,
    Scope.BEATMAPSETS: BeatmapsetListingSchema,
    Scope.SCORES: ...,
    Scope.QUEUES: QueueSchema,
    Scope.REQUESTS: RequestSchema
}

SCOPE_EXCLUDE_MAPPING = {
    Scope.BEATMAPS: ...,
    Scope.BEATMAPSETS: {
        "beatmapset_snapshot": {
            "beatmap_snapshots": {
                "__all__": {"beatmapset_snapshots", "leaderboard"}
            }
        }
    },
    Scope.SCORES: ...,
    Scope.QUEUES: {
        "requests": True,
        "managers": True
    },
    Scope.REQUESTS: {
        "beatmapset_snapshot": {
            "beatmap_snapshots": {
                "__all__": {"beatmapset_snapshots", "leaderboard"}
            }
        },
        "queue": {"requests", "managers"}
    }
}


class SearchEngine:
    def __init__(
        self,
        scope: Scope,
        search_terms: SearchTermsSchema | dict[str, Union[str, list[str], bool, dict[str, int]]] = None,
        sorting: SortingSchema | list[dict[str, str]] = None,
        filters: FiltersSchema | dict[str, dict[str, Union[dict[str, ConditionValue], ConditionValue, bool, None]]] = None,
        frontend_mode: bool = False
    ):
        self.scope = scope
        self.frontend_mode = frontend_mode
        self.model_class = SCOPE_MODEL_MAPPING[scope]
        self.schema_class = SCOPE_SCHEMA_MAPPING[scope]
        self.exclude = SCOPE_EXCLUDE_MAPPING[scope]

        if isinstance(search_terms, SearchTermsSchema) or search_terms is None:
            self.search_terms = search_terms
        elif isinstance(search_terms, dict):
            self.search_terms = SearchTermsSchema.model_validate(search_terms)
        else:
            raise TypeError(f"search_terms must be SearchTermsSchema or dict, got {type(search_terms).__name__}")

        if isinstance(sorting, SortingSchema) or sorting is None:
            self.sorting = sorting
        elif isinstance(sorting, list):
            self.sorting = SortingSchema.model_validate(sorting)
        else:
            raise TypeError(f"sorting must be SearchTermsSchema or dict, got {type(search_terms).__name__}")

        if isinstance(filters, FiltersSchema) or filters is None:
            self.filters = filters
        elif isinstance(filters, dict):
            self.filters = FiltersSchema.model_validate(filters)
        else:
            raise TypeError(f"filters must be FiltersSchema or dict, got {type(search_terms).__name__}")

        self.query: Optional[Select] = None
        self._compose_query()

    async def search(
        self,
        session: AsyncSession,
        limit: int = DEFAULT_LIMIT,
        offset: int = DEFAULT_OFFSET,
        debug: bool = False
    ) -> ResultsType:
        if not isinstance(limit, int) or not isinstance(offset, int) or limit < 0 or offset < 0:
            raise TypeError("Both limit and offset must be a positive integer")

        page_query = self.query.limit(limit).offset(offset)
        result = await session.execute(page_query)

        if debug and self.search_terms:
            self.print_score_debug(result.mappings())
            result = await session.execute(page_query)

        return result.scalars().all()

    def _compose_query(self):
        beatmap_snapshot_options = (
            selectinload(BeatmapSnapshot.beatmap_tags),
            selectinload(BeatmapSnapshot.owner_profiles),
            noload(BeatmapSnapshot.beatmapset_snapshots),
            noload(BeatmapSnapshot.leaderboard)
        )

        beatmapset_snapshot_options = (
            selectinload(BeatmapsetSnapshot.beatmap_snapshots)
            .options(*beatmap_snapshot_options),
            selectinload(BeatmapsetSnapshot.beatmapset_tags),
            joinedload(BeatmapsetSnapshot.user_profile)
        )

        queue_options = (
            noload(Queue.managers),
            joinedload(Queue.user_profile),
            selectinload(Queue.manager_profiles)
        )

        match self.scope:
            case Scope.BEATMAPS:
                self.query = (
                    select(BeatmapListing)
                    .join(BeatmapListing.beatmap_snapshot)
                    .options(
                        joinedload(BeatmapListing.beatmap_snapshot)
                        .options(*beatmap_snapshot_options)
                    )
                )
            case Scope.BEATMAPSETS:
                self.query: Select = (
                    select(BeatmapsetListing)
                    .join(BeatmapsetListing.beatmapset_snapshot)
                    .options(
                        joinedload(BeatmapsetListing.beatmapset_snapshot)
                        .options(*beatmapset_snapshot_options)
                    )
                )
            case Scope.QUEUES:
                self.query: Select = (
                    select(Queue)
                    .options(
                        *queue_options,
                        selectinload(Queue.requests)
                        .options(
                            joinedload(Request.beatmapset_snapshot)
                            .options(*beatmapset_snapshot_options),
                            noload(Request.user_profile),
                            noload(Request.queue)
                        )
                    )
                )
            case Scope.REQUESTS:
                self.query: Select = (
                    select(Request)
                    .join(Request.beatmapset_snapshot)
                    .options(
                        joinedload(Request.beatmapset_snapshot)
                        .options(*beatmapset_snapshot_options),
                        joinedload(Request.user_profile),
                        joinedload(Request.queue)
                        .options(
                            noload(Queue.requests),
                            *queue_options
                        )
                    )
                )

        if self.search_terms:
            self._apply_search_terms()

        if self.sorting:
            self._apply_sorting()

        if self.filters:
            self._apply_filters()

    def _apply_search_terms(self):
        filter_cte = search_terms_filtered_cte_factory(self.scope, self.search_terms)
        category_score_ctes = search_terms_scored_ctes_factory(self.scope, self.search_terms)

        match self.scope:
            case Scope.BEATMAPS:
                ...
            case Scope.BEATMAPSETS:
                beatmap_cte = category_score_ctes.get(SearchableFieldCategory.BEATMAP)
                beatmapset_cte = category_score_ctes.get(SearchableFieldCategory.BEATMAPSET)

                aggregated_beatmap_cte = (
                    aggregated_child_scores_to_parent_cte_factory(
                        child_score_cte=beatmap_cte,
                        mapping_table=beatmap_snapshot_beatmapset_snapshot_association,
                        mapping_child_fk="beatmap_snapshot_id",
                        mapping_parent_fk="beatmapset_snapshot_id",
                        cte_name="aggregated_beatmap_scores_cte",
                    )
                    if beatmap_cte is not None
                    else None
                )

                beatmap_score_column = (aggregated_beatmap_cte.c.score if aggregated_beatmap_cte is not None else literal_column("0"))
                beatmapset_score_column = (beatmapset_cte.c.score if beatmapset_cte is not None else literal_column("0"))

                total_score_column = (
                    func.coalesce(beatmap_score_column, 0) +
                    func.coalesce(beatmapset_score_column, 0)
                ).label("total_score")

                self.query = self.query.join(filter_cte,filter_cte.c.id == BeatmapsetSnapshot.id)

                if beatmap_cte is not None:
                    self.query = (
                        self.query
                        .outerjoin(aggregated_beatmap_cte, aggregated_beatmap_cte.c.id == BeatmapsetSnapshot.id)
                        .add_columns(aggregated_beatmap_cte.c.score_details.label("beatmap_score_details"))
                    )

                if beatmapset_cte is not None:
                    self.query = (
                        self.query
                        .outerjoin(beatmapset_cte, beatmapset_cte.c.id == BeatmapsetSnapshot.id)
                        .add_columns(beatmapset_cte.c.score_details.label("beatmapset_score_details"))
                    )

                self.query = (
                    self.query
                    .add_columns(total_score_column)
                    .order_by(total_score_column.desc())
                )
            case Scope.QUEUES:
                beatmap_cte = category_score_ctes.get(SearchableFieldCategory.BEATMAP)
                beatmapset_cte = category_score_ctes.get(SearchableFieldCategory.BEATMAPSET)
                queue_cte = category_score_ctes.get(SearchableFieldCategory.QUEUE)
                request_cte = category_score_ctes.get(SearchableFieldCategory.REQUEST)

                aggregated_beatmap_cte = (
                    aggregated_child_scores_to_parent_cte_factory(
                        child_score_cte=beatmap_cte,
                        mapping_table=beatmap_snapshot_beatmapset_snapshot_association,
                        mapping_child_fk="beatmap_snapshot_id",
                        mapping_parent_fk="beatmapset_snapshot_id",
                        cte_name="aggregated_beatmap_scores_cte",
                    )
                    if beatmap_cte is not None
                    else None
                )

                if aggregated_beatmap_cte is not None:
                    queue_from_beatmap_cte = aggregated_child_scores_to_parent_cte_factory(
                        aggregated_beatmap_cte,
                        Request.__table__,
                        "beatmapset_snapshot_id",
                        "queue_id",
                        "queue_aggregated_from_beatmap_scores_cte"
                    )
                else:
                    queue_from_beatmap_cte = None

                if beatmapset_cte is not None:
                    queue_from_beatmapset_cte = aggregated_child_scores_to_parent_cte_factory(
                        beatmapset_cte,
                        Request.__table__,
                        "beatmapset_snapshot_id",
                        "queue_id",
                        "queue_aggregated_from_beatmapset_scores_cte"
                    )
                else:
                    queue_from_beatmapset_cte = None

                if request_cte is not None:
                    queue_from_request_cte = aggregated_child_scores_to_parent_cte_factory(
                        request_cte,
                        Request.__table__,
                        "id",
                        "queue_id",
                        "queue_aggregated_from_request_scores_cte"
                    )
                else:
                    queue_from_request_cte = None

                beatmap_score_column = (queue_from_beatmap_cte.c.score if queue_from_beatmap_cte is not None else literal_column("0"))
                beatmapset_score_column = (queue_from_beatmapset_cte.c.score if queue_from_beatmapset_cte is not None else literal_column("0"))
                queue_score_column = (queue_cte.c.score if queue_cte is not None else literal_column("0"))
                request_score_column = (queue_from_request_cte.c.score if queue_from_request_cte is not None else literal_column("0"))

                total_score_column = (
                        func.coalesce(beatmap_score_column, 0) +
                        func.coalesce(beatmapset_score_column, 0) +
                        func.coalesce(queue_score_column, 0) +
                        func.coalesce(request_score_column, 0)
                ).label("total_score")

                self.query = self.query.join(filter_cte, filter_cte.c.id == Queue.id)

                if queue_from_beatmap_cte is not None:
                    self.query = (
                        self.query
                        .outerjoin(queue_from_beatmap_cte, queue_from_beatmap_cte.c.id == Queue.id)
                        .add_columns(queue_from_beatmap_cte.c.score_details.label("beatmap_score_details"))
                    )

                if queue_from_beatmapset_cte is not None:
                    self.query = (
                        self.query
                        .outerjoin(queue_from_beatmapset_cte, queue_from_beatmapset_cte.c.id == Queue.id)
                        .add_columns(queue_from_beatmapset_cte.c.score_details.label("beatmapset_score_details"))
                    )

                if queue_cte is not None:
                    self.query = (
                        self.query
                        .outerjoin(queue_cte, queue_cte.c.id == Queue.id)
                        .add_columns(queue_cte.c.score_details.label("queue_score_details"))
                    )

                if queue_from_request_cte is not None:
                    self.query = (
                        self.query
                        .outerjoin(queue_from_request_cte, queue_from_request_cte.c.id == Queue.id)
                        .add_columns(queue_from_request_cte.c.score_details.label("request_score_details"))
                    )

                self.query = (
                    self.query
                    .add_columns(total_score_column)
                    .order_by(total_score_column.desc())
                )

            case Scope.REQUESTS:
                beatmap_cte = category_score_ctes.get(SearchableFieldCategory.BEATMAP)
                beatmapset_cte = category_score_ctes.get(SearchableFieldCategory.BEATMAPSET)
                request_cte = category_score_ctes.get(SearchableFieldCategory.REQUEST)

                aggregated_beatmap_cte = (
                    aggregated_child_scores_to_parent_cte_factory(
                        child_score_cte=beatmap_cte,
                        mapping_table=beatmap_snapshot_beatmapset_snapshot_association,
                        mapping_child_fk="beatmap_snapshot_id",
                        mapping_parent_fk="beatmapset_snapshot_id",
                        cte_name="aggregated_beatmap_scores_cte",
                    )
                    if beatmap_cte is not None
                    else None
                )

                beatmap_score_column = (aggregated_beatmap_cte.c.score if aggregated_beatmap_cte is not None else literal_column("0"))
                beatmapset_score_column = (beatmapset_cte.c.score if beatmapset_cte is not None else literal_column("0"))
                request_score_column = (request_cte.c.score if request_cte is not None else literal_column("0"))

                total_score_column = (
                        func.coalesce(beatmap_score_column, 0) +
                        func.coalesce(beatmapset_score_column, 0) +
                        func.coalesce(request_score_column, 0)
                ).label("total_score")

                self.query = self.query.join(filter_cte, filter_cte.c.id == Request.id)

                if beatmap_cte is not None:
                    self.query = (
                        self.query
                        .outerjoin(aggregated_beatmap_cte, aggregated_beatmap_cte.c.id == BeatmapsetSnapshot.id)
                        .add_columns(aggregated_beatmap_cte.c.score_details.label("beatmap_score_details"))
                    )

                if beatmapset_cte is not None:
                    self.query = (
                        self.query
                        .outerjoin(beatmapset_cte, beatmapset_cte.c.id == BeatmapsetSnapshot.id)
                        .add_columns(beatmapset_cte.c.score_details.label("beatmapset_score_details"))
                    )

                if request_cte is not None:
                    self.query = (
                        self.query
                        .outerjoin(request_cte, request_cte.c.id == Request.id)
                        .add_columns(request_cte.c.score_details.label("request_score_details"))
                    )

                self.query = (
                    self.query
                    .add_columns(total_score_column)
                    .order_by(total_score_column.desc())
                )

    def _apply_sorting(self):
        def apply_clause():
            sorting_clauses.append(sorting_option.order.sort_func(target))

        def apply_sorting_cte(cte: CTE):
            nonlocal target
            target = cte.c.target

            self.query = (
                self.query
                .join(cte, cte.c.id == self.model_class.value.id)
                .where(cte.c.rank == 1)
            )

            apply_clause()

        def apply_sorting_option():
            match category:
                case SearchableFieldCategory.PROFILE:
                    cte = profile_sorting_cte_factory(self.scope, sorting_option)
                    apply_sorting_cte(cte)
                case SearchableFieldCategory.BEATMAP:
                    cte = bm_ss_sorting_cte_factory(self.scope, sorting_option)
                    apply_sorting_cte(cte)
                case SearchableFieldCategory.BEATMAPSET:
                    cte = bms_ss_sorting_cte_factory(self.scope, sorting_option)
                    apply_sorting_cte(cte)
                case SearchableFieldCategory.QUEUE:
                    cte = queue_sorting_cte_factory(self.scope, sorting_option)
                    apply_sorting_cte(cte)
                case SearchableFieldCategory.REQUEST:
                    cte = request_sorting_cte_factory(self.scope, sorting_option)
                    apply_sorting_cte(cte)

        sorting_clauses = []

        for sorting_option in self.sorting:
            category = SearchableFieldCategory.from_model_class(sorting_option.field.model_class)
            target = sorting_option.field.target
            apply_sorting_option()

        if sorting_clauses:
            self.query = self.query.order_by(None).order_by(*sorting_clauses)

    def _apply_filters(self):
        def clause_generator(is_aggregated: bool = False) -> Generator[BinaryExpression, None, None]:
            for op_str, value in conditions.model_dump(exclude_unset=True, by_alias=True).items():
                filter_operator = FilterOperator.from_name(op_str)
                yield get_filter_condition(filter_operator, target, value, is_aggregated=is_aggregated)

        def apply_clauses():
            for clause in clause_generator():
                filtering_clauses.append(clause)

        def apply_filter_conditions():
            nonlocal target

            match field_category:
                case SearchableFieldCategory.PROFILE:
                    cte = profile_filtering_cte_factory(self.scope, target)
                    target = cte.c.target
                    self.query = self.query.join(cte, cte.c.id == self.model_class.value.id)
                    apply_clauses()
                case SearchableFieldCategory.BEATMAP:
                    aggregated_conditions = clause_generator(is_aggregated=True) if self.scope is not Scope.BEATMAPS else None
                    cte = bm_ss_filtering_cte_factory(self.scope, target, aggregated_conditions=aggregated_conditions)
                    self.query = self.query.join(cte, cte.c.id == self.model_class.value.id)

                    if aggregated_conditions is None:
                        apply_clauses()
                case SearchableFieldCategory.BEATMAPSET:
                    cte = bms_ss_filtering_cte_factory(self.scope, target)
                    target = cte.c.target
                    self.query = self.query.join(cte, cte.c.id == self.model_class.value.id)
                    apply_clauses()
                case SearchableFieldCategory.QUEUE:
                    cte = queue_filtering_cte_factory(self.scope, target)
                    target = cte.c.target
                    self.query = self.query.join(cte, cte.c.id == self.model_class.value.id)
                    apply_clauses()
                case SearchableFieldCategory.REQUEST:
                    cte = request_filtering_cte_factory(self.scope, target)
                    target = cte.c.target
                    self.query = self.query.join(cte, cte.c.id == self.model_class.value.id)
                    apply_clauses()

        filtering_clauses = []

        for category_name, field_filters in self.filters:
            if field_filters is None:
                continue

            for field_name, conditions in field_filters.root.items():
                model_field = ModelField.from_category_field(category_name, field_name)
                field_category = SearchableFieldCategory.from_model_class(model_field.model_class)
                target = model_field.target
                apply_filter_conditions()

        if filtering_clauses:
            self.query = self.query.where(and_(*filtering_clauses))

    def dump(self, page: ResultsType) -> list[dict[str, Any]]:
        if self.frontend_mode:
            include = self.schema_class.FRONTEND_INCLUDE
            exclude = None
        else:
            include = None
            exclude = self.exclude

        return [
            self.schema_class.model_validate(model).model_dump(
                include=include,
                exclude=exclude
            )
            for model in page
        ]

    def print_score_debug(self, result: MappingResult) -> None:
        model_name = self.model_class.value.__name__
        max_term_length = max(len(term) for term in self.search_terms.terms)
        spacer_length = 68 + max_term_length

        print("=" * spacer_length)
        print(f"{"=" * int((spacer_length / 2 - 7))}SEARCH RESULTS{"=" * int((spacer_length / 2 - 7 + (1 if spacer_length % 2 != 0 else 0)))}")

        for row in result:
            model = row[model_name]
            total_score = row["total_score"]
            print(f"{"=" * spacer_length}")
            print(f"{model_name} ID: {model.id} | Total Score: {total_score}")

            for category in CATEGORY_NAMES:
                if (key := f"{category}_score_details") in row and (score_details := row[key]):
                    print(f"\n[{category.capitalize()} Matches] | Score: {sum(match["score"] for match in score_details)}")

                    for match in sorted(score_details, key=lambda x: x["score"], reverse=True):
                        print(
                            f"  -> Term: {match["term"]:{max_term_length}} | "
                            f"Field: {match["field"]:14} | "
                            f"Pattern: {match["pattern"]:9} | "
                            f"Score: {match["score"]}"
                        )

        print("=" * spacer_length)

    @property
    def compiled_query(self) -> str:
        return str(self.query.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))
