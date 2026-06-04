import pytest

from app.daemon.services.service.task.backoff import (
    BackoffStrategy,
    ConstantBackoff,
    LinearBackoff,
    ExponentialBackoff,
)


class TestConstantBackoff:
    def test_next_delay_returns_constant_value(self):
        strategy = ConstantBackoff(delay=5.0)

        assert strategy.next_delay() == 5.0
        assert strategy.next_delay() == 5.0
        assert strategy.next_delay() == 5.0

    def test_reset_does_nothing(self):
        strategy = ConstantBackoff(delay=3.0)

        strategy.next_delay()
        strategy.reset()

        assert strategy.next_delay() == 3.0


class TestLinearBackoff:
    def test_next_delay_increases_linearly(self):
        strategy = LinearBackoff(step=1.0, max_delay=10.0)

        assert strategy.next_delay() == 1.0
        assert strategy.next_delay() == 2.0
        assert strategy.next_delay() == 3.0
        assert strategy.next_delay() == 4.0

    def test_next_delay_respects_max_delay(self):
        strategy = LinearBackoff(step=5.0, max_delay=12.0)

        assert strategy.next_delay() == 5.0
        assert strategy.next_delay() == 10.0
        assert strategy.next_delay() == 12.0
        assert strategy.next_delay() == 12.0

    def test_reset_resets_to_zero(self):
        strategy = LinearBackoff(step=2.0, max_delay=10.0)

        strategy.next_delay()
        strategy.next_delay()
        strategy.reset()

        assert strategy.next_delay() == 2.0

    def test_default_values(self):
        strategy = LinearBackoff()

        assert strategy.step == 1.0
        assert strategy.max_delay == 30.0
        assert strategy.next_delay() == 1.0


class TestExponentialBackoff:
    def test_next_delay_increases_exponentially(self):
        strategy = ExponentialBackoff(base=1.0, factor=2.0, max_delay=50.0)

        assert strategy.next_delay() == 1.0
        assert strategy.next_delay() == 2.0
        assert strategy.next_delay() == 4.0
        assert strategy.next_delay() == 8.0

    def test_next_delay_respects_max_delay(self):
        strategy = ExponentialBackoff(base=1.0, factor=2.0, max_delay=10.0)

        assert strategy.next_delay() == 1.0
        assert strategy.next_delay() == 2.0
        assert strategy.next_delay() == 4.0
        assert strategy.next_delay() == 8.0
        assert strategy.next_delay() == 10.0
        assert strategy.next_delay() == 10.0

    def test_reset_resets_to_base(self):
        strategy = ExponentialBackoff(base=2.0, factor=2.0, max_delay=20.0)

        strategy.next_delay()
        strategy.next_delay()
        strategy.reset()

        assert strategy.next_delay() == 2.0

    def test_default_values(self):
        strategy = ExponentialBackoff()

        assert strategy.base == 1.0
        assert strategy.factor == 2.0
        assert strategy.max_delay == 30.0
        assert strategy.next_delay() == 1.0


class TestBackoffStrategyInterface:
    def test_abstract_class_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            BackoffStrategy()
