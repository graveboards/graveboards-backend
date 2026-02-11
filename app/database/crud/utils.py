from sqlalchemy.orm.relationships import Relationship


def is_lazy(rel: Relationship) -> bool:
    return rel.lazy in {True, "select", "dynamic"}
