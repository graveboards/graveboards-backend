from functools import lru_cache

from app.database.models import ModelClass
from app.spec import load_spec


@lru_cache(maxsize=1)
def _get_spec_cached() -> dict:
    return load_spec()


def get_include_schema(model_class: ModelClass = None, schema_name: str = None) -> dict:
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
