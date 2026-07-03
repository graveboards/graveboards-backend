import re
import signal
import threading
from contextlib import contextmanager
from typing import Optional


class RegexTimeoutError(Exception):
    """Raised when regex evaluation exceeds the allowed time limit."""
    pass


_signal_lock = threading.Lock()


def _handle_timeout(signum, frame):
    """Signal handler that raises ``RegexTimeoutError`` on timeout."""
    raise RegexTimeoutError()


@contextmanager
def timeout_signal(seconds: float):
    """Context manager enforcing execution timeout using OS signals.

    Intended for protecting against catastrophic regex backtracking (ReDoS). Falls back
    silently if signals are unavailable on the platform. Uses a process-wide lock to
    prevent concurrent coroutines from interfering with each other's signal handlers.

    Args:
        seconds:
            Maximum allowed execution time.
    """
    with _signal_lock:
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
    except Exception as e:
        raise ValueError(f"Unexpected error during regex validation: {e}")
