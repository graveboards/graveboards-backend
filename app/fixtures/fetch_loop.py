"""Parameterized fetch loop for eliminating duplicate fetch methods.

Replaces the 6 near-duplicate fetch_* methods in FixtureDataFetcher with a single
parameterized FetchLoop that takes API call, ID generator, path builder, and
success/failure handlers as configuration.
"""

from typing import AsyncIterator, Callable, Coroutine
from pathlib import Path
from dataclasses import dataclass

from .fetcher import FetchEvent


@dataclass
class FetchConfig:
    """Configuration for a single fetch operation."""
    api_call: Callable[..., Coroutine]
    id_generator: Callable[..., Coroutine]
    path_builder: Callable[[int], Path]
    data_type: str
    success_handler: Callable[[int, dict], None]
    failure_handler: Callable[[int, Exception], None]
    max_retries: int = 10
    max_attempts: int = 100
    skip_existing: bool = True


class FetchLoop:
    """Parameterized fetch loop that yields progress events.

    Configures the fetch loop with API call, ID generator, path builder,
    and success/failure handlers. Yields FetchEvent progress updates.

    Example:
        loop = FetchLoop(
            api_call=lambda: oac.get_beatmap(beatmap_id),
            id_generator=lambda: get_random_id("beatmaps"),
            path_builder=lambda id: get_fixture_path("beatmaps") / f"beatmap_{id}.json",
            data_type="beatmap",
            success_handler=lambda id, data: save_fixture(id, data),
            failure_handler=lambda id, err: log_failure(id, err),
        )
        async for event in loop.run(target_count=50):
            update_progress(event)
    """

    def __init__(self, config: FetchConfig):
        self.config = config

    async def run(self, target_count: int, skip_existing: bool = True) -> AsyncIterator[FetchEvent]:
        """Run the fetch loop until target_count items are fetched.

        Args:
            target_count: Number of items to fetch
            skip_existing: Whether to skip already-seen IDs

        Yields:
            FetchEvent progress updates
        """
        fetched = 0
        attempts = 0

        while fetched < target_count and attempts < self.config.max_attempts:
            attempts += 1

            # Get next ID to try
            beatmap_id = await self.config.id_generator()

            # Skip if already seen
            if skip_existing and beatmap_id in self._seen_ids:
                continue

            # Try to fetch with retries
            retries = 0
            while retries < self.config.max_retries:
                try:
                    data = await self.config.api_call()

                    # Save the fixture
                    filepath = self.config.path_builder(beatmap_id)
                    self._atomic_write(filepath, data, self.config.data_type)

                    # Handle success
                    self.config.success_handler(beatmap_id, data)
                    fetched += 1
                    self._record_success()

                    yield FetchEvent(self.config.data_type, fetched, target_count)
                    break

                except Exception as e:
                    self._check_connection_stability(e)

                    # Handle 404 as skip
                    import httpx
                    if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 404:
                        self._add_failed_id(beatmap_id)
                        break

                    # Log and retry
                    retries += 1
                    if retries < self.config.max_retries:
                        beatmap_id = await self.config.id_generator()
                    else:
                        self.config.failure_handler(beatmap_id, e)
                        break

        if fetched < target_count:
            # Log warning if not all fetched
            pass

    def _atomic_write(self, filepath: Path, data: dict, data_type: str) -> None:
        """Write data to filepath atomically."""
        import json
        import os
        tmp_path = filepath.with_suffix(filepath.suffix + ".tmp")
        with open(tmp_path, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, filepath)

    def _check_connection_stability(self, error: Exception | None = None) -> None:
        """Track consecutive errors and fail fast on systemic issues."""
        import httpx
        if error is not None and isinstance(error, httpx.HTTPStatusError):
            return
        self._consecutive_errors = getattr(self, '_consecutive_errors', 0) + 1
        if self._consecutive_errors >= 5:
            raise ConnectionError(
                f"Consecutive connection errors ({self._consecutive_errors}) — "
                f"service appears unreachable. Aborting fetch."
            )

    def _record_success(self) -> None:
        """Reset consecutive error counter."""
        self._consecutive_errors = 0

    def _add_failed_id(self, id_: int) -> None:
        """Add ID to failed set (placeholder - subclasses should override)."""
        pass
