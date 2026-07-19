from connexion.exceptions import Forbidden


class RuleViolationError(Exception):
    def __init__(self, type: str, detail: str):
        self.type = type
        self._detail = detail
        super().__init__(detail)

    @property
    def detail(self) -> str:
        return self._detail


class RetryableValidationError(Exception):
    """A Tier-3 validation could not reach a terminal outcome.

    Raised when a transient/infrastructure failure (timeout, osu! API error,
    unexpected validator error) prevents deciding PASS vs VIOLATION. The work must
    NOT be marked completed so it can be retried, rather than silently accepting or
    rejecting the request.
    """

    def __init__(self, rule_types: list[str], detail: str = ""):
        self.rule_types = rule_types
        super().__init__(detail or f"Retryable validation error for: {rule_types}")
