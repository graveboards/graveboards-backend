import asyncio
import re
from typing import Optional


def safe_compile_regex(
        pattern: str,
        timeout: float = 0.1,
        sample: str = "a" * 100,
) -> Optional[re.Pattern]:
    """Safely compile a regular expression with timeout protection.

    Uses asyncio.wait_for to enforce a timeout on compilation and search.
    Falls back to None if the pattern causes catastrophic backtracking.

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
    """
    try:
        loop = asyncio.get_running_loop()
        compiled = loop.run_until_complete(
            asyncio.wait_for(
                asyncio.to_thread(re.compile, pattern),
                timeout=timeout,
            )
        )
        loop.run_until_complete(
            asyncio.wait_for(
                asyncio.to_thread(compiled.search, sample),
                timeout=timeout,
            )
        )
        return compiled
    except (asyncio.TimeoutError, re.error, Exception):
        return None
