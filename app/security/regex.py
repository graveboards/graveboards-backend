import re
import signal
from contextlib import contextmanager
from typing import Optional


class RegexTimeoutError(Exception):
    pass


def _handle_timeout(signum, frame):
    raise RegexTimeoutError()


@contextmanager
def timeout_signal(seconds: float):
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
