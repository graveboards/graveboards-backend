from enum import Enum
from typing import TypeVar

from .service import Service
from .score_fetcher import ScoreFetcher
from .profile_fetcher import ProfileFetcher
from .queue_request_handler import QueueRequestHandler

__all__ = [
    "ServiceType",
    "ServiceClass",
    "Service",
    "ScoreFetcher",
    "ProfileFetcher",
    "QueueRequestHandler"
]

ServiceType = TypeVar("ServiceType", bound=Service)


class ServiceClass(Enum):
    SCORE_FETCHER = ScoreFetcher
    PROFILE_FETCHER = ProfileFetcher
    QUEUE_REQUEST_HANDLER = QueueRequestHandler
