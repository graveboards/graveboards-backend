import re
import signal
from contextlib import contextmanager
from typing import Optional


class RegexTimeoutError(Exception):
    """Raised when regex evaluation exceeds the allowed time limit."""
    pass


def _handle_timeout(signum, frame):
    """Signal handler that raises ``RegexTimeoutError`` on timeout."""
    raise RegexTimeoutError()


@contextmanager
def timeout_signal(seconds: float):
    """Context manager enforcing execution timeout using OS signals.

    Intended for protecting against catastrophic regex backtracking (ReDoS). Falls back
    silently if signals are unavailable on the platform.

    Args:
        seconds:
            Maximum allowed execution time.
    """
    try:
        signal.signal(signal.SIGALRM, _handle_timeout)
        signal.setitimer(signal.ITIMER_REAL, seconds)
        yield
    except (AttributeError, ValueError):
        # Signals not available - skip timeout protection
        yield
    finally:
        try:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, signal.SIG_DFL)
        except (AttributeError, ValueError):
            pass


def safe_compile_regex(
        pattern: str,
        timeout: float = 0.1,
        sample: str = "a" * 100,
) -> Optional[re.Pattern]:
    """Safely compile a regular expression with timeout protection.

    Compiles the pattern and performs a sample search to detect catastrophic
    backtracking within a bounded time window.

    Args:
        pattern:
            Regex pattern string.
        timeout:
            Maximum allowed compilation/search time.
        sample:
            Sample string used to test execution safety.

    Returns:
        Compiled ``re.Pattern`` if valid and safe. ``None`` if an unexpected error
        occurs.

    Raises:
        ValueError:
            If pattern is invalid or compilation times out.
    """
    try:
        with timeout_signal(timeout):
            compiled = re.compile(pattern)
            compiled.search(sample)
            return compiled
    except RegexTimeoutError:
        raise ValueError("Regex compilation timed out (possible ReDoS)")
    except re.error as e:
        raise ValueError(f"Invalid regex: {e}")
    except Exception:
        return None
