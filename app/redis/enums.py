from enum import Enum

__all__ = [
    "ChannelName",
    "Namespace"
]


class ChannelName(Enum):
    SCORE_FETCHER_TASKS = "score_fetcher_tasks"
    PROFILE_FETCHER_TASKS = "profile_fetcher_tasks"
    QUEUE_REQUEST_HANDLER_TASKS = "queue_request_handler_tasks"


class Namespace(Enum):
    LOCK = "lock"
    RATE_LIMIT_COUNTER = "rate_limit_counter"
    OSU_CLIENT_OAUTH_TOKEN = "osu_client_oauth_token"
    OSU_USER_PROFILE = "osu_user_profile"
    CSRF_STATE = "csrf_state"
    QUEUE_REQUEST_HANDLER_TASK = "queue_request_handler_task"
    CACHED_BEATMAP = "cached_beatmap"
    CACHED_BEATMAPSET = "cached_beatmapset"

    def hash_name(self, suffix: int | str) -> str:
        return f"{self.value}:{suffix}"
