import pytest

from app.daemon.services.service.task.backoff import (
    BackoffStrategy,
    ConstantBackoff,
    LinearBackoff,
    ExponentialBackoff,
)


class TestConstantBackoff:
    """Test constant backoff strategy."""

    def test_next_delay_returns_constant_value(self):
        """Test that next_delay returns the configured constant delay."""
        strategy = ConstantBackoff(delay=5.0)

        assert strategy.next_delay() == 5.0
        assert strategy.next_delay() == 5.0
        assert strategy.next_delay() == 5.0

    def test_delay_value_can_be_zero(self):
        """Test that delay can be zero."""
        strategy = ConstantBackoff(delay=0.0)

        assert strategy.next_delay() == 0.0

    def test_delay_value_can_be_negative(self):
        """Test that delay can be negative (though not recommended)."""
        strategy = ConstantBackoff(delay=-1.0)

        assert strategy.next_delay() == -1.0

    def test_delay_with_float_precision(self):
        """Test delay with floating point precision."""
        strategy = ConstantBackoff(delay=0.5)

        assert strategy.next_delay() == 0.5

    def test_reset_does_nothing(self):
        """Test that reset() doesn't affect the delay."""
        strategy = ConstantBackoff(delay=3.0)

        strategy.next_delay()
        strategy.next_delay()
        strategy.reset()

        assert strategy.next_delay() == 3.0

    def test_multiple_instances_independent(self):
        """Test that multiple instances are independent."""
        strategy1 = ConstantBackoff(delay=2.0)
        strategy2 = ConstantBackoff(delay=5.0)

        assert strategy1.next_delay() == 2.0
        assert strategy2.next_delay() == 5.0
        assert strategy1.next_delay() == 2.0


class TestLinearBackoff:
    """Test linear backoff strategy."""

    def test_next_delay_increases_linearly(self):
        """Test that next_delay increases by step each call."""
        strategy = LinearBackoff(step=1.0, max_delay=10.0)

        assert strategy.next_delay() == 1.0
        assert strategy.next_delay() == 2.0
        assert strategy.next_delay() == 3.0
        assert strategy.next_delay() == 4.0

    def test_next_delay_respects_max_delay(self):
        """Test that next_delay stops at max_delay."""
        strategy = LinearBackoff(step=5.0, max_delay=12.0)

        assert strategy.next_delay() == 5.0
        assert strategy.next_delay() == 10.0
        assert strategy.next_delay() == 12.0
        assert strategy.next_delay() == 12.0

    def test_reset_resets_to_zero(self):
        """Test that reset() resets current delay to zero."""
        strategy = LinearBackoff(step=2.0, max_delay=10.0)

        strategy.next_delay()
        strategy.next_delay()

        assert strategy.next_delay() == 4.0

        strategy.reset()

        assert strategy.next_delay() == 2.0

    def test_default_values(self):
        """Test default values for step and max_delay."""
        strategy = LinearBackoff()

        assert strategy.step == 1.0
        assert strategy.max_delay == 30.0
        assert strategy.next_delay() == 1.0

    def test_custom_step_value(self):
        """Test with custom step value."""
        strategy = LinearBackoff(step=3.5, max_delay=20.0)

        assert strategy.next_delay() == 3.5
        assert strategy.next_delay() == 7.0
        assert strategy.next_delay() == 10.5

    def test_zero_step(self):
        """Test with zero step (behaves like constant)."""
        strategy = LinearBackoff(step=0.0, max_delay=10.0)

        assert strategy.next_delay() == 0.0
        assert strategy.next_delay() == 0.0

    def test_step_larger_than_max(self):
        """Test when step is larger than max_delay."""
        strategy = LinearBackoff(step=50.0, max_delay=10.0)

        assert strategy.next_delay() == 10.0
        assert strategy.next_delay() == 10.0


class TestExponentialBackoff:
    """Test exponential backoff strategy."""

    def test_next_delay_increases_exponentially(self):
        """Test that next_delay increases exponentially."""
        strategy = ExponentialBackoff(base=1.0, factor=2.0, max_delay=50.0)

        assert strategy.next_delay() == 1.0
        assert strategy.next_delay() == 2.0
        assert strategy.next_delay() == 4.0
        assert strategy.next_delay() == 8.0

    def test_next_delay_respects_max_delay(self):
        """Test that next_delay stops at max_delay."""
        strategy = ExponentialBackoff(base=1.0, factor=2.0, max_delay=10.0)

        assert strategy.next_delay() == 1.0
        assert strategy.next_delay() == 2.0
        assert strategy.next_delay() == 4.0
        assert strategy.next_delay() == 8.0
        assert strategy.next_delay() == 10.0
        assert strategy.next_delay() == 10.0

    def test_reset_resets_to_base(self):
        """Test that reset() resets to base value."""
        strategy = ExponentialBackoff(base=2.0, factor=2.0, max_delay=20.0)

        strategy.next_delay()
        strategy.next_delay()

        assert strategy.next_delay() == 4.0

        strategy.reset()

        assert strategy.next_delay() == 2.0

    def test_default_values(self):
        """Test default values for base, factor, and max_delay."""
        strategy = ExponentialBackoff()

        assert strategy.base == 1.0
        assert strategy.factor == 2.0
        assert strategy.max_delay == 30.0
        assert strategy.next_delay() == 1.0

    def test_custom_base_value(self):
        """Test with custom base value."""
        strategy = ExponentialBackoff(base=0.5, factor=2.0, max_delay=20.0)

        assert strategy.next_delay() == 0.5
        assert strategy.next_delay() == 1.0
        assert strategy.next_delay() == 2.0

    def test_custom_factor_value(self):
        """Test with custom factor value."""
        strategy = ExponentialBackoff(base=1.0, factor=3.0, max_delay=100.0)

        assert strategy.next_delay() == 1.0
        assert strategy.next_delay() == 3.0
        assert strategy.next_delay() == 9.0
        assert strategy.next_delay() == 27.0

    def test_factor_of_one(self):
        """Test with factor of 1 (behaves like constant)."""
        strategy = ExponentialBackoff(base=5.0, factor=1.0, max_delay=100.0)

        assert strategy.next_delay() == 5.0
        assert strategy.next_delay() == 5.0
        assert strategy.next_delay() == 5.0

    def test_base_larger_than_max(self):
        """Test when base is larger than max_delay."""
        strategy = ExponentialBackoff(base=50.0, factor=2.0, max_delay=10.0)

        assert strategy.next_delay() == 10.0
        assert strategy.next_delay() == 10.0


class TestBackoffStrategyInterface:
    """Test backoff strategy interface."""

    def test_abstract_class_cannot_be_instantiated(self):
        """Test that BackoffStrategy is abstract."""
        with pytest.raises(TypeError):
            BackoffStrategy()

    def test_concrete_implementations_instantiate(self):
        """Test that concrete implementations can be instantiated."""
        constant = ConstantBackoff(delay=1.0)
        linear = LinearBackoff()
        exponential = ExponentialBackoff()

        assert constant is not None
        assert linear is not None
        assert exponential is not None

    def test_all_implementations_have_next_delay(self):
        """Test that all implementations have next_delay method."""
        strategies = [
            ConstantBackoff(delay=1.0),
            LinearBackoff(),
            ExponentialBackoff(),
        ]

        for strategy in strategies:
            assert hasattr(strategy, "next_delay")
            assert callable(strategy.next_delay)

    def test_all_implementations_have_reset(self):
        """Test that all implementations have reset method."""
        strategies = [
            ConstantBackoff(delay=1.0),
            LinearBackoff(),
            ExponentialBackoff(),
        ]

        for strategy in strategies:
            assert hasattr(strategy, "reset")
            assert callable(strategy.reset)
