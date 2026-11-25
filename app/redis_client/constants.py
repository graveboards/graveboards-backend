"""Redis locking and connection constants."""

from __future__ import annotations

LOCK_EXPIRY = 10
LOCK_ACQUISITION_TIMEOUT = 10
LOCK_ACQUISITION_RETRY_INTERVAL = 1
CACHED_BEATMAP_EXPIRY = 3600
CACHED_BEATMAPSET_EXPIRY = 3600
# Terminal queue-request task hashes are kept this long after completion so a late
# reader still finds them; Redis then reclaims the key.
TASK_RETENTION_SECONDS = 86400
