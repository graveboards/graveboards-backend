from __future__ import annotations

import hashlib
import json
from typing import Any


def config_fingerprint(config: dict[str, Any] | None) -> str:
    """Return a stable short hash of a rule config.

    Used to give each rule its own Redis state namespace so two rules of
    the same stateful type - which are explicitly allowed - do not share a counter or
    cooldown timestamp. Two rules with identical configs produce the same fingerprint,
    but those are rejected as duplicates at write time, so a collision here is benign.

    Args:
        config:
            The rule's config dict (flat, JSON-serializable values).

    Returns:
        A 12-character hex fingerprint.
    """
    canonical = json.dumps(config or {}, sort_keys=True, default=str)
    return hashlib.sha1(canonical.encode()).hexdigest()[:12]
