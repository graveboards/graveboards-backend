import asyncio
import re
from typing import Optional


async def safe_compile_regex(
        pattern: str,
        timeout: float = 0.1,
        sample: str = "a" * 100,
) -> Optional[re.Pattern]:
    """Safely compile a regular expression with timeout protection.

    Uses asyncio.to_thread to run blocking regex operations in a thread pool,
    with asyncio.wait_for to enforce a timeout. Falls back to None if the
    pattern causes catastrophic backtracking.

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
        compiled = await asyncio.wait_for(
            asyncio.to_thread(re.compile, pattern),
            timeout=timeout,
        )
        await asyncio.wait_for(
            asyncio.to_thread(compiled.search, sample),
            timeout=timeout,
        )
        return compiled
    except (asyncio.TimeoutError, re.error, Exception):
        return None
