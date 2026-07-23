from collections.abc import Callable

from .service import Service

type ServiceFactory = Callable[[], Service]
