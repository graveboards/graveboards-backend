from typing import TypeAlias, Union, Literal

from sqlalchemy.sql import select, union_all, and_, exists
from sqlalchemy.sql.selectable import CTE, Select
from sqlalchemy.orm import InstrumentedAttribute

from app.database.models import (
    beatmap_snapshot_beatmapset_snapshot_association,
    BeatmapSnapshot,
    BeatmapsetSnapshot,
    Request,
    Queue
)
from app.search.mappings import SCOPE_CATEGORIES_MAPPING, CATEGORY_MODEL_FIELDS_MAPPING
from app.search.enums import Scope, SearchableFieldCategory
from app.search.datastructures import SearchTermsSchema
from .hashable_cte import HashableCTE
from .utils import extract_cte_target_scalar

TermName: TypeAlias = str


def search_terms_filtered_cte_factory(
    scope: Scope,
    search_terms: SearchTermsSchema
) -> CTE:
    """Build a CTE that filters entities by requiring all search terms to match.

    For the given scope, generates per-term subqueries across all configured searchable
    categories and fields. Each term produces a CTE of matching entity IDs (via
    LIKE/ILIKE depending on case sensitivity).

    The resulting CTE returns distinct IDs that appear in every term CTE (logical AND
    across terms, logical OR across fields/categories per term).

    Args:
        scope:
            The search ``Scope``.
        search_terms:
            Structured search term configuration.

    Returns:
        A CTE yielding distinct entity IDs that satisfy all terms.
    """
    categories = SCOPE_CATEGORIES_MAPPING[scope]
    terms = search_terms.terms
    field_weights = search_terms.field_weights
    like_operator: Literal["like", "ilike"] = "like" if search_terms.case_sensitive else "ilike"
    term_ctes: dict[TermName, CTE] = {}
    
    for term in terms:
        term_queries = []

        for category in categories:
            model_fields = CATEGORY_MODEL_FIELDS_MAPPING[category]
            weights = getattr(field_weights, category.value)

            for field, model_field in model_fields.items():
                model_class = model_field.model_class
                target = model_field.target
                weight = getattr(weights, field)
                pattern = f"%{term}%"

                if weight is None:
                    continue

                if isinstance(target, HashableCTE):
                    target = extract_cte_target_scalar(target.cte, model_class, id_column_label="beatmapset_snapshot_id", use_alias=True)

                term_queries.append(get_filter_stmt(scope, category, target, like_operator, pattern))

            if term_queries:
                term_cte = union_all(*term_queries).cte(f"term_{term}_ids_cte")
                term_ctes[term] = term_cte

    filter_cte = (
        select(term_ctes[terms[0]].c.id)
        .where(
            and_(
                *[
                    exists()
                    .where(term_ctes[terms[0]].c.id == term_ctes[term].c.id)
                    for term in terms[1:]
                ]
            )
        )
        .distinct()
        .cte("filter_cte")
    )

    return filter_cte


def get_filter_stmt(
    scope: Scope,
    category: SearchableFieldCategory,
    target: Union[InstrumentedAttribute, HashableCTE],
    like_operator: Literal["like", "ilike"],
    pattern: str
) -> Select:
    """Construct a scope-aware SELECT statement for filtering by a pattern.

    Produces a DISTINCT ID query for the given scope and searchable category, joining
    through required relationships when the target field lives on a related model.

    Args:
        scope:
            The active search scope determining the root entity.
        category:
            The searchable field category being queried.
        target:
            The SQLAlchemy attribute or extracted CTE scalar to filter on.
        like_operator:
            SQL operator to use (``"like"`` or ``"ilike"``).
        pattern:
            The wildcard pattern to apply.

    Returns:
        A SELECT statement yielding distinct root entity IDs that match.
    """
    match scope:
        case Scope.BEATMAPS:
            match category:
                case SearchableFieldCategory.BEATMAP:
                    stmt = (
                        select(BeatmapSnapshot.id)
                        .distinct()
                        .where(getattr(target, like_operator)(pattern))
                    )
                case SearchableFieldCategory.BEATMAPSET:
                    stmt = (
                        select(BeatmapSnapshot.id)
                        .join(
                            beatmap_snapshot_beatmapset_snapshot_association,
                            beatmap_snapshot_beatmapset_snapshot_association.c.beatmap_snapshot_id == BeatmapSnapshot.id
                        )
                        .join(
                            BeatmapsetSnapshot,
                            BeatmapsetSnapshot.id == beatmap_snapshot_beatmapset_snapshot_association.c.beatmapset_snapshot_id
                        )
                        .where(getattr(target, like_operator)(pattern))
                        .distinct()
                    )
                case _:
                    raise ValueError(f"Unsupported category for scope {scope}: {category}")
        case Scope.BEATMAPSETS:
            match category:
                case SearchableFieldCategory.BEATMAP:
                    stmt = (
                        select(BeatmapsetSnapshot.id)
                        .join(
                            beatmap_snapshot_beatmapset_snapshot_association,
                            beatmap_snapshot_beatmapset_snapshot_association.c.beatmapset_snapshot_id == BeatmapsetSnapshot.id
                        )
                        .join(
                            BeatmapSnapshot,
                            BeatmapSnapshot.id == beatmap_snapshot_beatmapset_snapshot_association.c.beatmap_snapshot_id
                        )
                        .where(getattr(target, like_operator)(pattern))
                        .distinct()
                    )
                case SearchableFieldCategory.BEATMAPSET:
                    stmt = (
                        select(BeatmapsetSnapshot.id)
                        .where(getattr(target, like_operator)(pattern))
                        .distinct()
                    )
                case _:
                    raise ValueError(f"Unsupported category for scope {scope}: {category}")
        case Scope.QUEUES:
            match category:
                case SearchableFieldCategory.BEATMAP:
                    stmt = (
                        select(Queue.id)
                        .join(Queue.requests)
                        .join(
                            BeatmapsetSnapshot,
                            BeatmapsetSnapshot.beatmapset_id == Request.beatmapset_id
                        )
                        .join(
                            beatmap_snapshot_beatmapset_snapshot_association,
                            beatmap_snapshot_beatmapset_snapshot_association.c.beatmapset_snapshot_id == BeatmapsetSnapshot.id
                        )
                        .join(
                            BeatmapSnapshot,
                            BeatmapSnapshot.id == beatmap_snapshot_beatmapset_snapshot_association.c.beatmap_snapshot_id
                        )
                        .where(getattr(target, like_operator)(pattern))
                        .distinct()
                    )
                case SearchableFieldCategory.BEATMAPSET:
                    stmt = (
                        select(Queue.id)
                        .join(Queue.requests)
                        .join(
                            BeatmapsetSnapshot,
                            BeatmapsetSnapshot.beatmapset_id == Request.beatmapset_id
                        )
                        .where(getattr(target, like_operator)(pattern))
                        .distinct()
                    )
                case SearchableFieldCategory.QUEUE:
                    stmt = (
                        select(Queue.id)
                        .where(getattr(target, like_operator)(pattern))
                        .distinct()
                    )
                case SearchableFieldCategory.REQUEST:
                    stmt = (
                        select(Queue.id)
                        .join(Queue.requests)
                        .where(getattr(target, like_operator)(pattern))
                        .distinct()
                    )
                case _:
                    raise ValueError(f"Unsupported category for scope {scope}: {category}")
        case Scope.REQUESTS:
            match category:
                case SearchableFieldCategory.BEATMAP:
                    stmt = (
                        select(Request.id)
                        .join(
                            BeatmapsetSnapshot,
                            BeatmapsetSnapshot.beatmapset_id == Request.beatmapset_id
                        )
                        .join(
                            beatmap_snapshot_beatmapset_snapshot_association,
                            beatmap_snapshot_beatmapset_snapshot_association.c.beatmapset_snapshot_id == BeatmapsetSnapshot.id
                        )
                        .join(
                            BeatmapSnapshot,
                            BeatmapSnapshot.id == beatmap_snapshot_beatmapset_snapshot_association.c.beatmap_snapshot_id
                        )
                        .where(getattr(target, like_operator)(pattern))
                        .distinct()
                    )
                case SearchableFieldCategory.BEATMAPSET:
                    stmt = (
                        select(Request.id)
                        .join(
                            BeatmapsetSnapshot,
                            BeatmapsetSnapshot.beatmapset_id == Request.beatmapset_id
                        )
                        .where(getattr(target, like_operator)(pattern))
                        .distinct()
                    )
                case SearchableFieldCategory.REQUEST:
                    stmt = (
                        select(Request.id)
                        .where(getattr(target, like_operator)(pattern))
                        .distinct()
                    )
                case _:
                    raise ValueError(f"Unsupported category for scope {scope}: {category}")
        case _:
            raise ValueError(f"Unsupported scope: {scope}")

    return stmt
