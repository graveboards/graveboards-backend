import logging


class Logger(logging.LoggerAdapter):
    """Structured logger adapter with contextual enrichment.

    Extends ``logging.LoggerAdapter`` to merge per-instance context with per-call
    ``extra`` fields, allowing structured logging with consistent metadata injection.
    """

    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        """Merge adapter-level and call-level context.

        Args:
            msg:
                Log message.
            kwargs:
                Logging keyword arguments.

        Returns:
            Tuple of (message, updated kwargs) with merged ``extra`` data.
        """
        extra = kwargs.get("extra", {})
        merged = {**self.extra, **extra}
        kwargs["extra"] = merged
        return msg, kwargs
