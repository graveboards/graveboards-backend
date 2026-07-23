from connexion import request

from app.config import DEV_ADMIN_USER_ID

DEV_IDENTITY_HEADER = "X-Debug-User-Id"


def resolve_dev_caller_id() -> int:
    """Resolve the caller identity to use when ``DISABLE_SECURITY`` is set.

    Only ever called when security is disabled (never in prod - see the boot
    guard in ``app.connexion_app``), so there is no real authenticated caller
    to derive an ID from. Instead of leaving authorization checks with nothing
    to check against, this stands in a real (seeded) user ID so role/ownership
    logic runs exactly as it would in prod, just against a dev identity.

    Defaults to ``DEV_ADMIN_USER_ID`` so the existing "just works" dev
    experience is preserved without any extra setup. Pass the
    ``X-Debug-User-Id`` header to impersonate a different user (e.g.
    ``DEV_USER_ID``, a seeded non-admin) to exercise non-admin code paths.
    """
    header_value = request.headers.get(DEV_IDENTITY_HEADER)

    if header_value is not None:
        try:
            return int(header_value)
        except ValueError:
            pass

    return DEV_ADMIN_USER_ID
