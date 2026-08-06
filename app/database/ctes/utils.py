"""Shared helpers for building search CTEs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy.orm import aliased
from sqlalchemy.sql import select

if TYPE_CHECKING:
    from sqlalchemy.sql.selectable import CTE, ScalarSelect
    from sqlalchemy.sql.selectable import Alias as AliasType

    from app.database.models import ModelClass


def extract_cte_target_scalar(
    cte: CTE, model_class: ModelClass[Any], id_column_label: str = "id", use_alias: bool = False
) -> ScalarSelect:
    """Extract a correlated scalar subquery from a (id, target) CTE.

    Converts a projection-style CTE into a scalar value usable as a field target in
    filtering or scoring queries. The returned subquery selects ``cte.target`` where the
    CTE's ID matches the model's primary key.

    Optionally aliases the CTE to avoid name collisions when reused multiple times in
    the same query.

    Args:
        cte:
            CTE exposing at least (id, target) columns.
        model_class:
            ORM model whose primary key is used for correlation.
        id_column_label:
            Column name in the CTE representing the entity ID.
        use_alias:
            Whether to alias the CTE before correlation.

    Returns:
    -------
        A correlated ScalarSelect suitable for use in WHERE clauses.
    """
    pk_column = model_class.mapper.primary_key[0]

    aliased_cte: CTE | AliasType = aliased(cte) if use_alias else cte  # type: ignore[assignment]

    return (
        select(aliased_cte.c.target)
        .where(aliased_cte.c[id_column_label] == pk_column)
        .scalar_subquery()
    )
