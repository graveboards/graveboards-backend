"""Parameterized fetch loop for eliminating duplicate fetch methods.

Replaces the 6 near-duplicate fetch_* methods in FixtureDataFetcher with a single
parameterized FetchLoop that takes API call, ID generator, path builder, and
success/failure handlers as configuration.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import AsyncIterator, Callable, Coroutine, Any
from dataclasses import dataclass, field

import httpx

from app.exceptions import clean_error_msg


class FetchEvent:
    def __init__(self, category: str, current: int, total: int):
        self.category = category
        self.current = current
        self.total = total


@dataclass
class FetchConfig:
    """Configuration for a single fetch operation."""

    api_call: Callable[[int], Coroutine]
    id_generator: Callable[[], Coroutine[int]]
    path_builder: Callable[[int], Path]
    data_type: str
    success_handler: Callable[..., Any]
    failure_handler: Callable[..., Any]
    skip_checker: Callable[[int], bool]
    max_retries: int = 10
    max_attempts: int = 100
    on_error: Callable[[Exception], None] | None = None
    data_validator: Callable[[dict], bool] | None = None
    on_empty_data: Callable[[int], None] | None = None
    on_empty_data_limit: int | None = None


class FetchLoop:
    """Parameterized fetch loop that yields progress events.

    Configures the fetch loop with API call, ID generator, path builder,
    and success/failure handlers. Yields FetchEvent progress updates.
    """

    def __init__(self, config: FetchConfig):
        self.config = config

    async def _call_handler(self, handler: Callable[..., Any], *args: Any) -> None:
        """Call a handler, awaiting it if it's a coroutine function."""
        result = handler(*args)
        if asyncio.iscoroutine(result):
            await result

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
        consecutive_empty = 0
        max_consecutive_empty = self.config.on_empty_data_limit or float("inf")

        while fetched < target_count and attempts < self.config.max_attempts:
            attempts += 1

            beatmap_id = await self.config.id_generator()

            if skip_existing and self.config.skip_checker(beatmap_id):
                continue

            retries = 0
            while retries < self.config.max_retries:
                try:
                    data = await self.config.api_call(beatmap_id)

                    if self.config.data_validator and not self.config.data_validator(data):
                        consecutive_empty += 1
                        if self.config.on_empty_data:
                            self.config.on_empty_data(beatmap_id)
                        if consecutive_empty >= max_consecutive_empty:
                            break
                        retries += 1
                        continue
                    consecutive_empty = 0

                    filepath = self.config.path_builder(beatmap_id)
                    self._atomic_write(filepath, data, self.config.data_type)

                    await self._call_handler(self.config.success_handler, beatmap_id, data)
                    fetched += 1
                    self._record_success()

                    yield FetchEvent(self.config.data_type, fetched, target_count)
                    break

                except Exception as e:
                    if not isinstance(e, httpx.HTTPStatusError):
                        if self.config.on_error:
                            self.config.on_error(e)

                    if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 404:
                        await self._call_handler(self.config.failure_handler, beatmap_id, e)
                        break

                    await self._call_handler(self.config.failure_handler, beatmap_id, e)
                    retries += 1
                    if retries < self.config.max_retries:
                        beatmap_id = await self.config.id_generator()

        if fetched < target_count:
            pass

    def _atomic_write(self, filepath: Path, data: dict, data_type: str) -> None:
        """Write data to filepath atomically."""
        from .validation import validate_data

        if data_type:
            is_valid, error_msg = validate_data(data, data_type)
            if not is_valid:
                pass

        tmp_path = filepath.with_suffix(filepath.suffix + ".tmp")
        with open(tmp_path, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, filepath)

    def _record_success(self) -> None:
        """Reset consecutive error counter (no-op, handled by callbacks)."""
        pass
