from enum import StrEnum

__all__ = [
    "ChannelName",
    "Namespace"
]


class ChannelName(StrEnum):
    """Redis pub/sub channel names used by background workers."""
    SCORE_FETCHER_TASKS = "score_fetcher_tasks"
    PROFILE_FETCHER_TASKS = "profile_fetcher_tasks"
    QUEUE_REQUEST_HANDLER_TASKS = "queue_request_handler_tasks"


class Namespace(StrEnum):
    """Redis key namespaces for logical separation of data."""
    LOCK = "lock"
    RATE_LIMIT_COUNTER = "rate_limit_counter"
    OSU_CLIENT_OAUTH_TOKEN = "osu_client_oauth_token"
    OSU_USER_PROFILE = "osu_user_profile"
    CSRF_STATE = "csrf_state"
    QUEUE_REQUEST_HANDLER_TASK = "queue_request_handler_task"
    CACHED_BEATMAP = "cached_beatmap"
    CACHED_BEATMAPSET = "cached_beatmapset"

    def hash_name(self, suffix: int | str) -> str:
        """Build a namespaced Redis key.

        Args:
            suffix:
                Unique identifier appended to the namespace.

        Returns:
            Fully-qualified Redis key string.
        """
        return f"{self.value}:{suffix}"
