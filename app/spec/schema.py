from functools import lru_cache

from app.database.models import ModelClass
from app.spec import load_spec


@lru_cache(maxsize=1)
def _get_spec_cached() -> dict:
    """Return a cached in-memory instance of the OpenAPI specification.

    Wraps ``load_spec`` with an LRU cache to avoid repeated disk I/O and rebuild checks
    within the same process.

    Returns:
        dict: The OpenAPI specification.
    """
    return load_spec()


def get_filter_schema(
    model_class: ModelClass = None,
    schema_name: str = None,
) -> dict:
    """Retrieve a Filter schema from the OpenAPI specification.

    Exactly one of ``model_class`` or ``schema_name`` must be provided.

    Args:
        model_class:
            Enum value representing a model.
        schema_name:
            Explicit schema name.

    Returns:
        dict:
            The requested schema definition.

    Raises:
        ValueError:
            If arguments are invalid or schema is not found.

    """
    return _get_schema_by_suffix(
        suffix="Filter",
        model_class=model_class,
        schema_name=schema_name,
    )


def get_include_schema(
    model_class: ModelClass = None,
    schema_name: str = None,
) -> dict:
    """Retrieve an Include schema from the OpenAPI specification.

    Exactly one of ``model_class`` or ``schema_name`` must be provided.

    Args:
        model_class:
            Enum value representing a model.
        schema_name:
            Explicit schema name.

    Returns:
        dict:
            The requested schema definition.

    Raises:
        ValueError:
            If arguments are invalid or schema is not found.

    """
    return _get_schema_by_suffix(
        "Include",
        model_class=model_class,
        schema_name=schema_name,
    )


def _get_schema_by_suffix(
    suffix: str,
    *,
    model_class: ModelClass = None,
    schema_name: str = None,
) -> dict:
    """Retrieve a schema from the OpenAPI spec using a suffix convention.

    Exactly one of ``model_class`` or ``schema_name`` must be provided.
    If ``model_class`` is given, the schema name is derived by appending
    the provided suffix to the model class name.

    Args:
        suffix:
            Required schema suffix (e.g., ``"Include"``, ``"Filter"``).
        model_class:
            Enum value representing a model.
        schema_name:
            Explicit schema name ending with the provided suffix.

    Returns:
        dict:
            The requested schema definition.

    Raises:
        ValueError:
            If arguments are invalid or schema is not found.
    """
    if model_class is not None and schema_name is not None:
        raise ValueError("Must provide one of either model_class or schema_name, not both")

    if isinstance(model_class, ModelClass):
        schema_name = model_class.value.__name__ + suffix
    elif isinstance(schema_name, str):
        if not schema_name.endswith(suffix):
            raise ValueError(f"schema_name must end with '{suffix}'")
    else:
        raise ValueError("Must provide either model_class (ModelClass) or schema_name (str)")

    spec = _get_spec_cached()
    schema = spec["components"]["schemas"].get(schema_name)

    if not schema:
        raise ValueError(f"Schema with name '{schema_name}' not found")

    return schema

