from sqlalchemy.sql.functions import func
from sqlalchemy.sql.elements import literal_column

from app.database.models import BeatmapSnapshot, BeatmapsetSnapshot, Queue, Request, beatmap_snapshot_beatmapset_snapshot_association
from app.search.enums import Scope, SearchableFieldCategory
from app.database.ctes.search_terms_scored import aggregated_child_scores_to_parent_cte_factory


def _apply_beatmaps_relevance(select_stmt, category_score_ctes, search_terms):
    """Apply relevance ordering for BEATMAPS scope."""
    beatmap_cte = category_score_ctes.get(SearchableFieldCategory.BEATMAP)
    beatmapset_cte = category_score_ctes.get(SearchableFieldCategory.BEATMAPSET)

    aggregated_beatmapset_cte = (
        aggregated_child_scores_to_parent_cte_factory(
            child_score_cte=beatmapset_cte,
            mapping_table=beatmap_snapshot_beatmapset_snapshot_association,
            mapping_child_fk="beatmapset_snapshot_id",
            mapping_parent_fk="beatmap_snapshot_id",
            cte_name="aggregated_beatmapset_scores_cte",
        )
        if beatmapset_cte is not None
        else None
    )

    beatmap_score_column = (beatmap_cte.c.score if beatmap_cte is not None else literal_column("0"))
    beatmapset_score_column = (aggregated_beatmapset_cte.c.score if aggregated_beatmapset_cte is not None else literal_column("0"))

    total_score_column = (
        func.coalesce(beatmap_score_column, 0) +
        func.coalesce(beatmapset_score_column, 0)
    ).label("total_score")

    if beatmap_cte is not None:
        select_stmt = select_stmt.outerjoin(beatmap_cte, beatmap_cte.c.id == BeatmapSnapshot.id)

    if aggregated_beatmapset_cte is not None:
        select_stmt = select_stmt.outerjoin(aggregated_beatmapset_cte, aggregated_beatmapset_cte.c.id == BeatmapSnapshot.id)

    return select_stmt.order_by(None).order_by(total_score_column.desc())


def _apply_beatmapsets_relevance(select_stmt, category_score_ctes, search_terms):
    """Apply relevance ordering for BEATMAPSETS scope."""
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

    if aggregated_beatmap_cte is not None:
        select_stmt = select_stmt.outerjoin(aggregated_beatmap_cte, aggregated_beatmap_cte.c.id == BeatmapsetSnapshot.id)

    if beatmapset_cte is not None:
        select_stmt = select_stmt.outerjoin(beatmapset_cte, beatmapset_cte.c.id == BeatmapsetSnapshot.id)

    return select_stmt.order_by(None).order_by(total_score_column.desc())


def _apply_queues_relevance(select_stmt, category_score_ctes, search_terms):
    """Apply relevance ordering for QUEUES scope."""
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

    if queue_from_beatmap_cte is not None:
        select_stmt = select_stmt.outerjoin(queue_from_beatmap_cte, queue_from_beatmap_cte.c.id == Queue.id)

    if queue_from_beatmapset_cte is not None:
        select_stmt = select_stmt.outerjoin(queue_from_beatmapset_cte, queue_from_beatmapset_cte.c.id == Queue.id)

    if queue_cte is not None:
        select_stmt = select_stmt.outerjoin(queue_cte, queue_cte.c.id == Queue.id)

    if queue_from_request_cte is not None:
        select_stmt = select_stmt.outerjoin(queue_from_request_cte, queue_from_request_cte.c.id == Queue.id)

    return select_stmt.order_by(None).order_by(total_score_column.desc())


def _apply_requests_relevance(select_stmt, category_score_ctes, search_terms):
    """Apply relevance ordering for REQUESTS scope."""
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

    if aggregated_beatmap_cte is not None:
        select_stmt = select_stmt.outerjoin(aggregated_beatmap_cte, aggregated_beatmap_cte.c.id == Request.beatmapset_snapshot_id)

    if beatmapset_cte is not None:
        select_stmt = select_stmt.outerjoin(beatmapset_cte, beatmapset_cte.c.id == Request.beatmapset_snapshot_id)

    if request_cte is not None:
        select_stmt = select_stmt.outerjoin(request_cte, request_cte.c.id == Request.id)

    return select_stmt.order_by(None).order_by(total_score_column.desc())


SCOPE_RELEVANCE_HANDLERS = {
    Scope.BEATMAPS: _apply_beatmaps_relevance,
    Scope.BEATMAPSETS: _apply_beatmapsets_relevance,
    Scope.QUEUES: _apply_queues_relevance,
    Scope.REQUESTS: _apply_requests_relevance,
}
