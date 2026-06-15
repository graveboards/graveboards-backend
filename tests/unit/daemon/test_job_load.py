import pytest
from datetime import datetime, timezone

from app.daemon.services.service.job.load import JobLoadInstruction


class TestJobLoadInstruction:
    """Test JobLoadInstruction dataclass."""

    def test_create_with_execution_time(self):
        """Test creating instruction with execution_time."""
        execution_time = datetime.now(timezone.utc)
        instruction = JobLoadInstruction(execution_time=execution_time)

        assert instruction.execution_time == execution_time
        assert instruction.last_execution is None
        assert instruction.interval_hours is None
        assert instruction.skip is False

    def test_create_with_last_execution(self):
        """Test creating instruction with last_execution."""
        last_execution = datetime.now(timezone.utc)
        instruction = JobLoadInstruction(last_execution=last_execution)

        assert instruction.execution_time is None
        assert instruction.last_execution == last_execution
        assert instruction.interval_hours is None
        assert instruction.skip is False

    def test_create_with_all_fields(self):
        """Test creating instruction with all fields."""
        execution_time = datetime.now(timezone.utc)
        last_execution = datetime.now(timezone.utc)
        instruction = JobLoadInstruction(
            execution_time=execution_time,
            last_execution=last_execution,
            interval_hours=24.0,
            skip=True
        )

        assert instruction.execution_time == execution_time
        assert instruction.last_execution == last_execution
        assert instruction.interval_hours == 24.0
        assert instruction.skip is True

    def test_create_with_defaults(self):
        """Test creating instruction with default values."""
        instruction = JobLoadInstruction()

        assert instruction.execution_time is None
        assert instruction.last_execution is None
        assert instruction.interval_hours is None
        assert instruction.skip is False

    def test_interval_hours_as_float(self):
        """Test interval_hours accepts float values."""
        instruction = JobLoadInstruction(interval_hours=12.5)

        assert instruction.interval_hours == 12.5

    def test_skip_is_boolean(self):
        """Test skip is boolean."""
        instruction1 = JobLoadInstruction(skip=True)
        instruction2 = JobLoadInstruction(skip=False)

        assert instruction1.skip is True
        assert instruction2.skip is False

    def test_frozen_attribute_cannot_be_modified(self):
        """Test that instruction is immutable."""
        instruction = JobLoadInstruction()

        with pytest.raises(Exception):
            instruction.execution_time = datetime.now(timezone.utc)

    def test_slots_for_memory_efficiency(self):
        """Test that instruction uses slots."""
        instruction = JobLoadInstruction()

        with pytest.raises(AttributeError):
            instruction.new_attr = "value"

    def test_equality_with_same_values(self):
        """Test equality comparison with same values."""
        execution_time = datetime.now(timezone.utc)
        instruction1 = JobLoadInstruction(execution_time=execution_time)
        instruction2 = JobLoadInstruction(execution_time=execution_time)

        assert instruction1 == instruction2

    def test_inequality_with_different_values(self):
        """Test inequality comparison with different values."""
        instruction1 = JobLoadInstruction(
            execution_time=datetime(2026, 1, 1, tzinfo=timezone.utc)
        )
        instruction2 = JobLoadInstruction(
            execution_time=datetime(2026, 1, 2, tzinfo=timezone.utc)
        )

        assert instruction1 != instruction2

    def test_none_vs_zero_delay_interval(self):
        """Test difference between None and zero interval_hours."""
        instruction1 = JobLoadInstruction(interval_hours=None)
        instruction2 = JobLoadInstruction(interval_hours=0.0)

        assert instruction1.interval_hours is None
        assert instruction2.interval_hours == 0.0
        assert instruction1 != instruction2

    def test_none_execution_time_vs_zero_timestamp(self):
        """Test difference between None and timestamp."""
        timestamp = datetime(1970, 1, 1, tzinfo=timezone.utc)
        instruction1 = JobLoadInstruction(execution_time=None)
        instruction2 = JobLoadInstruction(execution_time=timestamp)

        assert instruction1.execution_time is None
        assert instruction2.execution_time == timestamp
        assert instruction1 != instruction2

    def test_hashability(self):
        """Test that instruction is hashable."""
        instruction = JobLoadInstruction(
            execution_time=datetime(2026, 1, 1, tzinfo=timezone.utc)
        )

        instruction_set = {instruction}
        assert instruction in instruction_set

    def test_string_representation(self):
        """Test string representation."""
        execution_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
        instruction = JobLoadInstruction(execution_time=execution_time)

        repr_str = repr(instruction)

        assert "JobLoadInstruction" in repr_str
        assert "2026" in repr_str

    def test_instruction_with_only_skip_true(self):
        """Test instruction with only skip flag."""
        instruction = JobLoadInstruction(skip=True)

        assert instruction.skip is True
        assert instruction.execution_time is None
        assert instruction.last_execution is None
        assert instruction.interval_hours is None

    def test_multiple_instructions_independent(self):
        """Test that multiple instructions are independent."""
        instruction1 = JobLoadInstruction(execution_time=datetime(2026, 1, 1, tzinfo=timezone.utc))
        instruction2 = JobLoadInstruction(execution_time=datetime(2026, 1, 2, tzinfo=timezone.utc))

        assert instruction1.execution_time != instruction2.execution_time

    def test_instruction_with_negative_interval(self):
        """Test instruction with negative interval_hours."""
        instruction = JobLoadInstruction(interval_hours=-1.0)

        assert instruction.interval_hours == -1.0

    def test_instruction_with_very_large_interval(self):
        """Test instruction with very large interval."""
        instruction = JobLoadInstruction(interval_hours=8760.0)

        assert instruction.interval_hours == 8760.0

    def test_instruction_datetime_timezone_aware(self):
        """Test that datetime must be timezone-aware."""
        utc_time = datetime.now(timezone.utc)
        instruction = JobLoadInstruction(execution_time=utc_time)

        assert instruction.execution_time.tzinfo is not None
