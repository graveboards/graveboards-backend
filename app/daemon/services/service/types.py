from typing import Callable

from .service import Service

type ServiceFactory = Callable[[], Service]
