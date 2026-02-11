import yaml

from connexion.spec import resolve_refs

from app.config import SPEC_DIR, OPENAPI_ENTRYPOINT, DISABLE_SECURITY
from .shallow import populate_shallow_refs
from .include import get_include_schema

with open(OPENAPI_ENTRYPOINT, "r") as f:
    openapi_spec = resolve_refs(yaml.full_load(f), base_uri=f"{SPEC_DIR}/")

populate_shallow_refs(openapi_spec)

if DISABLE_SECURITY:
    openapi_spec.pop("security", None)

    for path in openapi_spec.get("paths", {}).values():
        for method in path.values():
            method.pop("security", None)
