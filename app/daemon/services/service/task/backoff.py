"""Backoff strategies for retry logic."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BackoffStrategy(ABC):
    """Abstract base class for backoff strategies.

    Subclasses define how the delay between retries increases over time.
    """

    @abstractmethod
    def next_delay(self) -> float:
        """Return the next delay in seconds."""

    @abstractmethod
    def reset(self) -> None:
        """Reset the strategy to its initial state."""


class ConstantBackoff(BackoffStrategy):
    """A backoff strategy that returns a constant delay.

    Attributes:
        delay:
            The constant delay in seconds.
    """

    def __init__(self, delay: float) -> None:
        """Initialize with a constant delay.

        Args:
            delay:
                Delay in seconds between retries.
        """
        self.delay = delay

    def next_delay(self) -> float:
        """Return the constant delay."""
        return self.delay

    def reset(self) -> None:
        """No-op for constant backoff."""


class LinearBackoff(BackoffStrategy):
    """A backoff strategy that increases delay linearly.

    Attributes:
        step:
            Increment added to the delay each call.
        max_delay:
            Maximum delay cap in seconds.
    """

    def __init__(
        self,
        step: float = 1.0,
        max_delay: float = 30.0,
    ) -> None:
        """Initialize with step and max delay.

        Args:
            step:
                Increment added to the delay each call.
            max_delay:
                Maximum delay cap in seconds.
        """
        self.step = step
        self.max_delay = max_delay
        self._current = 0.0

    def next_delay(self) -> float:
        """Return the current delay and increment for the next call."""
        self._current = min(self._current + self.step, self.max_delay)
        return self._current

    def reset(self) -> None:
        """Reset the delay to zero."""
        self._current = 0.0


class ExponentialBackoff(BackoffStrategy):
    """A backoff strategy that increases delay exponentially.

    Attributes:
        base:
            Starting delay in seconds.
        factor:
            Multiplier applied to the delay each call.
        max_delay:
            Maximum delay cap in seconds.
    """

    def __init__(
        self,
        base: float = 1.0,
        factor: float = 2.0,
        max_delay: float = 30.0,
    ) -> None:
        """Initialize with base, factor, and max delay.

        Args:
            base:
                Starting delay in seconds.
            factor:
                Multiplier applied to the delay each call.
            max_delay:
                Maximum delay cap in seconds.
        """
        self.base = base
        self.factor = factor
        self.max_delay = max_delay
        self._current = base

    def next_delay(self) -> float:
        """Return the current delay and multiply for the next call."""
        delay = self._current
        self._current = min(self._current * self.factor, self.max_delay)
        return delay

    def reset(self) -> None:
        """Reset the delay to the base value."""
        self._current = self.base
