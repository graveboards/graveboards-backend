from __future__ import annotations
from collections.abc import Callable

from .service import Service

type ServiceFactory = Callable[[], Service]
