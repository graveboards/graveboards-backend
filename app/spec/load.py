import os
import pickle
import yaml

from connexion.spec import resolve_refs

from app.enums import Env
from app.config import ENV, DISABLE_SECURITY, SPEC_DIR, CACHE_FILE, OPENAPI_ENTRYPOINT
from .shallow import populate_shallow_refs


def load_spec() -> dict:
    cache_exists = os.path.exists(CACHE_FILE)

    if not cache_exists:
        return _build_spec()

    if ENV is Env.PROD:
        with open(CACHE_FILE, "rb") as f:
            payload = pickle.load(f)

        return payload["spec"]

    cache_mtime = os.path.getmtime(CACHE_FILE)
    latest_spec_mtime = _get_latest_spec_mtime()

    with open(CACHE_FILE, "rb") as f:
        payload = pickle.load(f)

    cached_options = payload.get("build_options", {})

    if (
        cache_mtime < latest_spec_mtime
        or cached_options != _current_build_options()
    ):
        return _build_spec()

    return payload["spec"]


def _build_spec() -> dict:
    with open(OPENAPI_ENTRYPOINT, "r") as f:
        spec = resolve_refs(yaml.full_load(f), base_uri=f"{SPEC_DIR}/")

    _apply_mutations(spec)

    cache_payload = {
        "spec": spec,
        "build_options": _current_build_options()
    }

    with open(CACHE_FILE, "wb") as f:
        pickle.dump(cache_payload, f)

    return spec


def _apply_mutations(spec: dict):
    populate_shallow_refs(spec)

    if DISABLE_SECURITY and ENV is not Env.PROD:
        spec.pop("security", None)

        for path in spec.get("paths", {}).values():
            for method in path.values():
                method.pop("security", None)


def _current_build_options() -> dict:
    return {
        "env": ENV,
        "disable_security": DISABLE_SECURITY
    }


def _get_latest_spec_mtime() -> float:
    latest = 0.0

    for root, _, files in os.walk(SPEC_DIR):
        for file in files:
            if file.endswith((".yaml", ".yml")):
                path = os.path.join(root, file)
                latest = max(latest, os.path.getmtime(path))

    return latest
