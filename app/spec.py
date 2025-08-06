import yaml

from connexion.spec import resolve_refs

from .config import SPEC_DIR, OPENAPI_ENTRYPOINT, DISABLE_SECURITY

with open(OPENAPI_ENTRYPOINT, "r") as f:
    openapi_spec = resolve_refs(yaml.full_load(f), base_uri=f"{SPEC_DIR}/")

if DISABLE_SECURITY:
    openapi_spec.pop("security", None)

    for path in openapi_spec.get("paths", {}).values():
        for method in path.values():
            method.pop("security", None)
