from sqlalchemy.sql import select
from sqlalchemy.sql.selectable import ScalarSelect, CTE
from sqlalchemy.orm import aliased

from app.database.models import ModelClass


def extract_cte_target_scalar(cte: CTE, model_class: ModelClass, id_column_label: str = "id", use_alias: bool = False) -> ScalarSelect:
    pk_column = model_class.mapper.primary_key[0]
    cte = aliased(cte) if use_alias else cte

    return (
        select(cte.c.target)
        .where(cte.c[id_column_label] == pk_column)
        .scalar_subquery()
    )
