import pytest
from unittest.mock import MagicMock

from app.daemon.services.service.task import (
    TaskRetryPolicy,
)
from app.daemon.services.service.task.backoff import ConstantBackoff


class TestTaskRetryPolicy:
    """Test TaskRetryPolicy dataclass."""

    def test_create_policy_with_all_options(self):
        """Test creating a policy with all options."""
        from app.daemon.services.service.task.backoff import (
            ConstantBackoff,
        )

        backoff = ConstantBackoff(delay=5.0)
        on_failure = MagicMock()
        on_max_retries_exceeded = MagicMock()

        policy = TaskRetryPolicy(
            backoff=backoff,
            max_retries=3,
            on_failure=on_failure,
            on_max_retries_exceeded=on_max_retries_exceeded
        )

        assert policy.backoff is backoff
        assert policy.max_retries == 3
        assert policy.on_failure is on_failure
        assert policy.on_max_retries_exceeded is on_max_retries_exceeded

    def test_create_policy_with_none_options(self):
        """Test creating a policy with None options."""
        policy = TaskRetryPolicy()

        assert policy.backoff is None
        assert policy.max_retries is None
        assert policy.on_failure is None
        assert policy.on_max_retries_exceeded is None

    def test_create_policy_with_minimal_options(self):
        """Test creating a policy with minimal options."""
        from app.daemon.services.service.task.backoff import (
            LinearBackoff,
        )

        policy = TaskRetryPolicy(backoff=LinearBackoff())

        assert policy.backoff is not None
        assert policy.max_retries is None
        assert policy.on_failure is None
        assert policy.on_max_retries_exceeded is None

    def test_policy_is_frozen(self):
        """Test that policy is immutable (frozen dataclass)."""
        from app.daemon.services.service.task.backoff import (
            ConstantBackoff,
        )

        backoff = ConstantBackoff(delay=1.0)
        policy = TaskRetryPolicy(backoff=backoff, max_retries=5)

        with pytest.raises(Exception):
            policy.max_retries = 10

    def test_policy_is_slotted(self):
        """Test that policy uses slots for memory efficiency."""
        from app.daemon.services.service.task.backoff import (
            ConstantBackoff,
        )

        backoff = ConstantBackoff(delay=1.0)
        policy = TaskRetryPolicy(backoff=backoff)

        with pytest.raises(AttributeError):
            policy.new_attr = "value"

    def test_policy_with_only_max_retries(self):
        """Test policy with only max_retries set."""
        policy = TaskRetryPolicy(max_retries=10)

        assert policy.backoff is None
        assert policy.max_retries == 10
        assert policy.on_failure is None
        assert policy.on_max_retries_exceeded is None

    def test_policy_with_failure_hook_only(self):
        """Test policy with only failure hook."""
        on_failure = MagicMock()
        policy = TaskRetryPolicy(on_failure=on_failure)

        assert policy.backoff is None
        assert policy.max_retries is None
        assert policy.on_failure is on_failure
        assert policy.on_max_retries_exceeded is None

    def test_policy_equality(self):
        """Test policy equality comparison."""
        from app.daemon.services.service.task.backoff import (
            ConstantBackoff,
        )

        backoff = ConstantBackoff(delay=5.0)
        on_failure = MagicMock()
        on_max_retries = MagicMock()

        policy1 = TaskRetryPolicy(
            backoff=backoff,
            max_retries=3,
            on_failure=on_failure,
            on_max_retries_exceeded=on_max_retries
        )

        policy2 = TaskRetryPolicy(
            backoff=backoff,
            max_retries=3,
            on_failure=on_failure,
            on_max_retries_exceeded=on_max_retries
        )

        # Dataclasses with same values should be equal
        assert policy1 == policy2

    def test_policy_inequality(self):
        """Test policy inequality comparison."""
        from app.daemon.services.service.task.backoff import (
            ConstantBackoff,
        )

        policy1 = TaskRetryPolicy(backoff=ConstantBackoff(delay=5.0))
        policy2 = TaskRetryPolicy(backoff=ConstantBackoff(delay=10.0))

        assert policy1 != policy2

    def test_policy_string_representation(self):
        """Test policy string representation."""
        from app.daemon.services.service.task.backoff import (
            ConstantBackoff,
        )

        backoff = ConstantBackoff(delay=5.0)
        policy = TaskRetryPolicy(
            backoff=backoff,
            max_retries=3
        )

        repr_str = repr(policy)

        assert "TaskRetryPolicy" in repr_str
        assert "5.0" in repr_str
        assert "3" in repr_str

    def test_policy_hashability(self):
        """Test that policy is hashable (due to frozen=True)."""
        from app.daemon.services.service.task.backoff import (
            ConstantBackoff,
        )

        backoff = ConstantBackoff(delay=5.0)
        policy = TaskRetryPolicy(backoff=backoff, max_retries=3)

        # Should be hashable due to frozen=True
        policy_set = {policy}
        assert policy in policy_set

    def test_policy_none_backoff_vs_zero_delay(self):
        """Test difference between None backoff and zero delay."""
        policy1 = TaskRetryPolicy(backoff=None, max_retries=5)
        policy2 = TaskRetryPolicy(
            backoff=ConstantBackoff(delay=0.0),
            max_retries=5
        )

        assert policy1.backoff is None
        assert policy2.backoff is not None
        assert policy2.backoff.delay == 0.0

        assert policy1 != policy2
