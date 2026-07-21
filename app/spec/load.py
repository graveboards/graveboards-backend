import os
import pickle
import yaml

from connexion.spec import resolve_refs

from app.enums import Env
from app.config import ENV, get_security_enabled, SPEC_DIR, CACHE_FILE, OPENAPI_ENTRYPOINT
from app.logging import get_logger
from .shallow import populate_shallow_refs

logger = get_logger(__name__)


def load_spec() -> dict:
    """Load the OpenAPI specification with environment-aware caching.

    In production, always returns the cached spec if present. In non-production
    environments, invalidates the cache when any YAML spec file has a newer modification
    time, or the current build options differ from those stored in the cache.

    If the cache is missing or invalid, rebuilds the spec and refreshes the cache.

    Returns:
        dict: The fully built and mutation-applied OpenAPI specification.
    """
    cache_exists = os.path.exists(CACHE_FILE)

    if not cache_exists:
        return _build_spec()

    if ENV == Env.PROD:
        try:
            with open(CACHE_FILE, "rb") as f:
                payload = pickle.load(f)
        except (pickle.UnpicklingError, EOFError, ValueError, OSError) as e:
            logger.warning(f"Corrupted spec cache at {CACHE_FILE}, rebuilding: {e}")
            return _build_spec()

        return payload["spec"]

    cache_mtime = os.path.getmtime(CACHE_FILE)
    latest_spec_mtime = _get_latest_spec_mtime()

    try:
        with open(CACHE_FILE, "rb") as f:
            payload = pickle.load(f)
    except (pickle.UnpicklingError, EOFError, ValueError, OSError) as e:
        logger.warning(f"Corrupted spec cache at {CACHE_FILE}, rebuilding: {e}")
        return _build_spec()

    cached_options = payload.get("build_options", {})

    if (
        cache_mtime < latest_spec_mtime
        or cached_options != _current_build_options()
    ):
        return _build_spec()

    return payload["spec"]


def _build_spec() -> dict:
    """Build the OpenAPI specification from source files.

    Loads the entrypoint YAML, resolves `$ref` references, applies internal mutations,
    and writes the resulting spec to a cache file along with the current build options.

    Returns:
        dict: The fully resolved and mutated OpenAPI specification.
    """
    with open(OPENAPI_ENTRYPOINT, "r") as f:
        spec = resolve_refs(yaml.full_load(f), base_uri=f"{SPEC_DIR}/")

    _apply_mutations(spec)

    cache_payload = {
        "spec": spec,
        "build_options": _current_build_options()
    }

    try:
        with open(CACHE_FILE, "wb") as f:
            pickle.dump(cache_payload, f)
    except (OSError, PermissionError):
        logger.warning(f"Could not write spec cache to {CACHE_FILE}, continuing without caching")

    return spec


def _apply_mutations(spec: dict) -> None:
    """Apply post-processing mutations to the OpenAPI specification.

    This includes expanding shallow schema references and optionally removing security
    requirements when disabled in non-production environments.

    Args:
        spec:
            The OpenAPI specification to mutate in place.
    """
    populate_shallow_refs(spec)

    if not get_security_enabled() and ENV is not Env.PROD:
        spec.pop("security", None)

        for path in spec.get("paths", {}).values():
            for method in path.values():
                method.pop("security", None)


def _current_build_options() -> dict:
    """Return the current build options affecting spec generation.

    These options are embedded in the cache payload and used to determine whether a
    rebuild is required.

    Returns:
        dict: A mapping of build-relevant configuration values.
    """
    return {
        "env": ENV,
        "disable_security": not get_security_enabled()
    }


def _get_latest_spec_mtime() -> float:
    """Compute the latest modification time across all spec YAML files.

    Recursively scans the specification directory and returns the most recent
    modification timestamp among `.yaml` and `.yml` files.

    Returns:
        float: The latest modification time (as a Unix timestamp).
    """
    latest = 0.0

    for root, _, files in os.walk(SPEC_DIR):
        for file in files:
            if file.endswith((".yaml", ".yml")):
                path = os.path.join(root, file)
                latest = max(latest, os.path.getmtime(path))

    return latest
