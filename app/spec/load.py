"""OpenAPI spec loading with caching."""

from __future__ import annotations

import pickle
from pathlib import Path
from pickle import PickleError as _PickleError
from typing import Any
from typing import cast as typing_cast

import yaml
from connexion.spec import resolve_refs

from app.config import CACHE_FILE, ENV, OPENAPI_ENTRYPOINT, SPEC_DIR, get_security_enabled
from app.enums import Env
from app.observability.logging import get_logger

from .shallow import populate_shallow_refs

logger = get_logger(__name__)


def load_spec() -> dict[str, Any]:
    """Load the OpenAPI specification with environment-aware caching.

    In production, always returns the cached spec if present. In non-production
    environments, invalidates the cache when any YAML spec file has a newer modification
    time, or the current build options differ from those stored in the cache.

    If the cache is missing or invalid, rebuilds the spec and refreshes the cache.

    Returns:
    -------
        dict: The fully built and mutation-applied OpenAPI specification.
    """
    cache_path = Path(CACHE_FILE)
    cache_exists = cache_path.exists()

    if not cache_exists:
        return _build_spec()

    try:
        with cache_path.open("rb") as f:
            payload: dict[str, Any] = pickle.load(f)
    except (EOFError, _PickleError, OSError):  # fmt: skip
        logger.warning("Spec cache at %s is corrupt — rebuilding", CACHE_FILE)
        return _build_spec()

    if ENV.value == Env.PROD.value:
        return typing_cast("dict[str, Any]", payload["spec"])

    cache_mtime = cache_path.stat().st_mtime
    latest_spec_mtime = _get_latest_spec_mtime()

    cached_options = payload.get("build_options", {})

    if cache_mtime < latest_spec_mtime or cached_options != _current_build_options():
        return _build_spec()

    return typing_cast("dict[str, Any]", payload["spec"])


def _build_spec() -> dict[str, Any]:
    """Build the OpenAPI specification from source files.

    Loads the entrypoint YAML, resolves `$ref` references, applies internal mutations,
    and writes the resulting spec to a cache file along with the current build options.

    Returns:
    -------
        dict: The fully resolved and mutated OpenAPI specification.
    """
    with Path(OPENAPI_ENTRYPOINT).open() as f:
        spec: dict[str, Any] = resolve_refs(yaml.full_load(f), base_uri=f"{SPEC_DIR}/")

    _apply_mutations(spec)

    cache_payload = {"spec": spec, "build_options": _current_build_options()}

    try:
        with Path(CACHE_FILE).open("wb") as f:
            pickle.dump(cache_payload, f)
    except (OSError, PermissionError):  # fmt: skip
        logger.warning("Could not write spec cache to %s, continuing without caching", CACHE_FILE)

    return spec


def _apply_mutations(spec: dict[str, Any]) -> None:
    """Apply post-processing mutations to the OpenAPI specification.

    This includes expanding shallow schema references and optionally removing security
    requirements when disabled in non-production environments.

    Args:
        spec:
            The OpenAPI specification to mutate in place.
    """
    populate_shallow_refs(spec)

    if not get_security_enabled() and ENV.value != Env.PROD.value:
        spec.pop("security", None)

        for path in spec.get("paths", {}).values():
            for method in path.values():
                method.pop("security", None)


def _current_build_options() -> dict[str, Any]:
    """Return the current build options affecting spec generation.

    These options are embedded in the cache payload and used to determine whether a
    rebuild is required.

    Returns:
    -------
        dict: A mapping of build-relevant configuration values.
    """
    return {"env": ENV, "disable_security": not get_security_enabled()}


def _get_latest_spec_mtime() -> float:
    """Compute the latest modification time across all spec YAML files.

    Recursively scans the specification directory and returns the most recent
    modification timestamp among `.yaml` and `.yml` files.

    Returns:
    -------
        float: The latest modification time (as a Unix timestamp).
    """
    latest = 0.0

    for path in Path(SPEC_DIR).rglob("*"):
        if path.suffix in (".yaml", ".yml"):
            latest = max(latest, path.stat().st_mtime)

    return latest
