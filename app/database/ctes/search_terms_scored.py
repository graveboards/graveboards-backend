from collections import defaultdict
from typing import Generator

from sqlalchemy.sql import select, cast, union_all
from sqlalchemy.sql.elements import literal
from sqlalchemy.sql.sqltypes import Integer, String
from sqlalchemy.sql.selectable import CTE, Select, CompoundSelect
from sqlalchemy.sql.functions import func

from app.database.models import beatmap_snapshot_beatmapset_snapshot_association
from app.search.enums import Scope
from app.search.datastructures import SearchTermsSchema, SCOPE_CATEGORIES_MAPPING, CATEGORY_MODEL_FIELDS_MAPPING, CATEGORY_FIELD_GROUPS_MAPPING
from app.search.enums import SearchableFieldCategory
from .hashable_cte import HashableCTE
from .utils import extract_cte_target_scalar


def search_terms_scored_ctes_factory(
        scope: Scope,
        search_terms: SearchTermsSchema
) -> dict[SearchableFieldCategory, CTE]:
    category_score_stmts: dict[SearchableFieldCategory, list[Select]] = defaultdict(list)

    for category, score_stmt in generate_term_score_stmts(scope, search_terms):
        category_score_stmts[category].append(score_stmt)

    category_score_ctes: dict[SearchableFieldCategory, CTE] = {}

    for category, stmts in category_score_stmts.items():
        unioned = union_all(*stmts)

        processed = process_field_groups(unioned, category, CATEGORY_FIELD_GROUPS_MAPPING).subquery()  # TODO: Allow user to configure FIELD_GROUPS

        category_score_ctes[category] = (
            select(
                processed.c.id,
                func.sum(func.coalesce(processed.c.score, 0)).label("score"),
                func.jsonb_agg(
                    func.jsonb_build_object(
                        "field", processed.c.field,
                        "term", processed.c.term,
                        "pattern", processed.c.pattern,
                        "score", processed.c.score
                    )
                ).label("score_details")
            )
            .group_by(processed.c.id)
            .cte(f"{category.value}_score_cte")
        )

    return category_score_ctes


def generate_term_score_stmts(
        scope: Scope,
        search_terms: SearchTermsSchema
) -> Generator[tuple[SearchableFieldCategory, Select], None, None]:
    categories = SCOPE_CATEGORIES_MAPPING[scope]
    terms = search_terms.terms
    multipliers = search_terms.pattern_multipliers
    field_weights = search_terms.field_weights
    like_operator = "like" if search_terms.case_sensitive else "ilike"

    for category in categories:
        model_fields = CATEGORY_MODEL_FIELDS_MAPPING[category]
        weights = getattr(field_weights, category.value)

        for field, model_field in model_fields.items():
            model_class = model_field.model_class
            target = model_field.target
            weight = getattr(weights, field)
            pk_column = model_class.mapper.primary_key[0]

            if weight is None:
                continue

            if isinstance(target, HashableCTE):
                target = extract_cte_target_scalar(target.cte, model_class, id_column_label="beatmapset_snapshot_id", use_alias=True)

            for term in terms:
                pattern_stmts = []

                for pattern_name, pattern, multiplier in multipliers.get_patterns(term):
                    if multiplier is None:
                        continue

                    score_value = cast(weight * multiplier, Integer)

                    pattern_stmts.append(
                        select(
                            pk_column.label("id"),
                            literal(field).label("field"),
                            literal(term).label("term"),
                            literal(pattern_name).label("pattern"),
                            score_value.label("score")
                        )
                        .where(getattr(target, like_operator)(pattern))
                    )

                unioned = union_all(*pattern_stmts).subquery()

                ranked = select(
                    unioned.c.id,
                    unioned.c.field,
                    unioned.c.term,
                    unioned.c.pattern,
                    unioned.c.score,
                    func.row_number().over(
                        partition_by=[unioned.c.id, unioned.c.term],
                        order_by=unioned.c.score.desc()
                    ).label("rank")
                ).subquery(f"{category.value}_{field}_{term}_ranked_pattern_scores")

                score_stmt = select(
                    ranked.c.id,
                    ranked.c.field,
                    ranked.c.term,
                    ranked.c.pattern,
                    ranked.c.score
                ).where(ranked.c.rank == 1)

                yield category, score_stmt


def process_field_groups(
        base_query: CompoundSelect,
        category: SearchableFieldCategory,
        field_groups_config: dict[SearchableFieldCategory, dict[str, set[str]]]
) -> CompoundSelect:
    if not (field_groups := field_groups_config.get(category, {})):
        return base_query

    grouped_fields = {field for group in field_groups.values() for field in group}

    non_grouped = (
        select(base_query.c)
        .where(~base_query.c.field.in_(grouped_fields))
    )

    group_queries = []

    for group_name, fields in field_groups.items():
        group_query = (
            select(
                base_query.c.id,
                literal(group_name).label("field"),
                base_query.c.term,
                base_query.c.pattern,
                func.max(base_query.c.score).label("score")
            )
            .where(base_query.c.field.in_(fields))
            .group_by(base_query.c.id, base_query.c.term, base_query.c.pattern)
        )
        group_queries.append(group_query)

    return union_all(non_grouped, *group_queries)


def aggregated_beatmap_score_cte_factory(beatmap_cte: CTE) -> CTE:
    exploded = (
        select(
            beatmap_snapshot_beatmapset_snapshot_association.c.beatmapset_snapshot_id.label("id"),
            func.jsonb_array_elements(beatmap_cte.c.score_details).label("entry")
        )
        .select_from(
            beatmap_cte.join(
                beatmap_snapshot_beatmapset_snapshot_association,
                beatmap_snapshot_beatmapset_snapshot_association.c.beatmap_snapshot_id == beatmap_cte.c.id
            )
        )
        .subquery()

    )

    parsed = (
        select(
            exploded.c.id,
            func.cast(exploded.c.entry.op("->>")("field"), String).label("field"),
            func.cast(exploded.c.entry.op("->>")("term"), String).label("term"),
            func.cast(exploded.c.entry.op("->>")("pattern"), String).label("pattern"),
            func.cast(exploded.c.entry.op("->>")("score"), Integer).label("score")
        )
        .subquery()
    )

    ranked = (
        select(
            parsed,
            func.row_number()
            .over(
                partition_by=[parsed.c.id, parsed.c.field, parsed.c.term],
                order_by=parsed.c.score.desc()
            ).label("rank")
        )
        .subquery()
    )

    max_entries = (
        select(
            ranked.c.id,
            ranked.c.field,
            ranked.c.term,
            ranked.c.pattern,
            ranked.c.score
        )
        .where(ranked.c.rank == 1)
        .subquery()
    )

    return (
        select(
            max_entries.c.id,
            func.sum(max_entries.c.score).label("score"),
            func.jsonb_agg(
                func.jsonb_build_object(
                    "field", max_entries.c.field,
                    "term", max_entries.c.term,
                    "pattern", max_entries.c.pattern,
                    "score", max_entries.c.score
                )
            ).label("score_details")
        )
        .group_by(max_entries.c.id)
        .cte("aggregated_beatmap_scores_cte")
    )
