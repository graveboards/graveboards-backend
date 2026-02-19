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


def get_include_schema(model_class: ModelClass = None, schema_name: str = None) -> dict:
    """Retrieve an Include schema from the OpenAPI specification.

    Exactly one of ``model_class`` or ``schema_name`` must be provided.

    If ``model_class`` is given, the schema name is derived by appending ``"Include"``
    to the model's class name.

    Args:
        model_class:
            Enum value representing a model.
        schema_name:
            Explicit schema name ending with ``"Include"``.

    Returns:
        dict: The requested Include schema definition.

    Raises:
        ValueError:
            If arguments are invalid or the schema is not found.
    """
    if model_class is not None and schema_name is not None:
        raise ValueError("Both model_class and schema_name cannot be provided simultaneously")

    if isinstance(model_class, ModelClass):
        schema_name = model_class.value.__name__ + "Include"
    elif isinstance(schema_name, str):
        if not schema_name.endswith("Include"):
            raise ValueError("schema_name must end with 'Include'")
    else:
        raise ValueError("Must provide either model_class as ModelClass or schema_name as str")

    spec = _get_spec_cached()
    schema = spec["components"]["schemas"].get(schema_name)

    if not schema:
        raise ValueError(f"Schema with name '{schema_name}' not found")

    return schema
