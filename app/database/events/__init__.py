"""SQLAlchemy event listeners for database model side effects.

All event handlers are intentionally synchronous. They execute within the
SQLAlchemy event thread and perform blocking operations (raw SQL via the
synchronous ``Connection`` object, Redis publishes via a synchronous context
manager).

This is an accepted trade-off:

    - The side effects (Redis publishes, listing updates) are lightweight and
      non-critical — failures are logged as warnings, not raised.
    - Making them async would require ``asyncio.create_task`` or ``run_sync``
      wrappers, adding complexity without meaningful benefit for operations
      that complete in under a millisecond.
    - The synchronous ``Connection`` object available in ``before_insert`` /
      ``after_insert`` handlers is the natural API for this use case.

A future migration to async-aware event handling (or moving side effects out
of SQLAlchemy events into explicit service calls) is tracked as a long-term
refactoring.
"""
from .user import *
from .score_fetcher_task import *
from .beatmap_snapshot import *
from .beatmapset_snapshot import *
from .request import *

__all__ = []
