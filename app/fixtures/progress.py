from __future__ import annotations
"""Progress bar handler for fixture fetch operations."""

import contextlib
import logging

from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn

logger = logging.getLogger(__name__)


class ProgressBar:
    """Simple progress bar handler for fetch operations."""

    def __init__(self, no_progress: bool = False) -> None:
        self.no_progress = no_progress
        self._progress: Progress | None = None
        self._task_ids: dict[str, int] = {}

    def start(self) -> None:
        """Start the progress display."""
        if self.no_progress:
            return
        try:
            self._progress = Progress(
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TextColumn("({task.completed}/{task.total})"),
                TimeRemainingColumn(),
            )
            self._progress.start()
        except ImportError:
            pass

    def update(self, category: str, current: int, total: int) -> None:
        """Update progress for a category."""
        if self.no_progress or not self._progress:
            return

        try:
            if category not in self._task_ids:
                self._task_ids[category] = self._progress.add_task(
                    f"Fetched {category}", total=total
                )

            task_id = self._task_ids[category]
            self._progress.update(task_id, completed=current)
        except Exception:
            logger.debug("Failed to update progress bar", exc_info=True)

    def stop(self) -> None:
        """Stop the progress display."""
        if self._progress:
            with contextlib.suppress(Exception):
                self._progress.stop()
