from connexion.exceptions import Forbidden


class RuleViolationError(Exception):
    def __init__(self, type: str, detail: str):
        self.type = type
        self._detail = detail
        super().__init__(detail)

    @property
    def detail(self) -> str:
        return self._detail
