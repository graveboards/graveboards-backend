from abc import ABC, abstractmethod


class BackoffStrategy(ABC):
    @abstractmethod
    def next_delay(self) -> float:
        ...

    @abstractmethod
    def reset(self) -> None:
        ...


class ConstantBackoff(BackoffStrategy):
    def __init__(self, delay: float) -> None:
        self.delay = delay

    def next_delay(self) -> float:
        return self.delay

    def reset(self) -> None:
        pass


class LinearBackoff(BackoffStrategy):
    def __init__(
        self,
        step: float = 1.0,
        max_delay: float = 30.0,
    ) -> None:
        self.step = step
        self.max_delay = max_delay
        self._current = 0.0

    def next_delay(self) -> float:
        self._current = min(self._current + self.step, self.max_delay)
        return self._current

    def reset(self) -> None:
        self._current = 0.0


class ExponentialBackoff(BackoffStrategy):
    def __init__(
        self,
        base: float = 1.0,
        factor: float = 2.0,
        max_delay: float = 30.0,
    ) -> None:
        self.base = base
        self.factor = factor
        self.max_delay = max_delay
        self._current = base

    def next_delay(self) -> float:
        delay = self._current
        self._current = min(self._current * self.factor, self.max_delay)
        return delay

    def reset(self) -> None:
        self._current = self.base
