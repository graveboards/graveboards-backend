"""Development identity resolution for security-disabled mode."""

from __future__ import annotations

import jwt
from connexion import request

from app.config import DEV_ADMIN_USER_ID

DEV_IDENTITY_HEADER = "X-Debug-User-Id"


def _user_id_from_bearer() -> int | None:
    """Extract a user ID from an ``Authorization: Bearer <jwt>`` header.

    Only ever called when security is disabled, so the token is decoded without
    signature or claim verification - it is trusted purely as a transport for
    the caller's ``sub``. Any malformed/missing token yields ``None`` so the
    caller can fall through to the next resolution step.

    Returns:
        The ``sub`` claim as an int, or ``None`` if it cannot be resolved.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None

    parts = auth_header.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    try:
        payload = jwt.decode(
            parts[1].strip(),
            options={"verify_signature": False, "require": ["sub"]},
        )
        sub = payload.get("sub")
        return int(sub) if isinstance(sub, str) and sub.isdigit() else None
    except Exception:
        return None


def resolve_dev_caller_id() -> int:
    """Resolve the dev caller user ID from the request.

    Only ever called when ``DISABLE_SECURITY`` is set (never in prod - see the
    boot guard in ``app.connexion_app``), so there is no real authenticated
    caller to derive an ID from. Instead of leaving authorization checks with
    nothing to check against, this stands in a real user ID so role/ownership
    logic runs exactly as it would in prod, just against a dev identity.

    Resolution order:

        1. ``Authorization: Bearer <jwt>`` - the caller's real ``sub`` claim,
           decoded without verification. This makes dev behave like prod: the
           identity follows whoever the frontend logged in as, without needing
           the signature/secret machinery of real security.
        2. ``X-Debug-User-Id`` header - explicit impersonation for exercising
           non-admin code paths (e.g. ``DEV_USER_ID``, a seeded non-admin).
        3. ``DEV_ADMIN_USER_ID`` - preserves the "just works" dev experience
           for unauthenticated requests without any extra setup.

    Returns:
        The dev user ID to authorize the request against.
    """
    bearer_user_id = _user_id_from_bearer()
    if bearer_user_id is not None:
        return bearer_user_id

    header_value = request.headers.get(DEV_IDENTITY_HEADER)

    if header_value is not None:
        try:
            return int(header_value)
        except ValueError:
            pass

    return int(DEV_ADMIN_USER_ID)
