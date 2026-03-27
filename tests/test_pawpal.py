from datetime import date, timedelta

import pytest

from pawpal_system import (
	ConflictWarning,
	DailyScheduleGenerator,
	LightweightConflictDetector,
	Owner,
	Pet,
	ScheduledTask,
	Scheduler,
	Task,
)


def test_task_completion_changes_status() -> None:
	task = Task(description="Give meds", time_minutes=5, frequency="daily")

	assert task.completed is False
	task.mark_complete()
	assert task.completed is True


def test_add_task_increases_pet_task_count() -> None:
	pet = Pet(name="Mochi", species="dog")
	starting_count = len(pet.tasks)

	pet.add_task(Task(description="Morning walk", time_minutes=20, frequency="daily"))

	assert len(pet.tasks) == starting_count + 1


def test_sort_tasks_by_time_shortest_first() -> None:
	scheduler = Scheduler()
	tasks = [
		Task(description="Long", time_minutes=30, frequency="daily"),
		Task(description="Short", time_minutes=10, frequency="daily"),
		Task(description="Medium", time_minutes=20, frequency="daily"),
	]

	sorted_tasks = scheduler.sort_by_time(tasks)

	assert [task.description for task in sorted_tasks] == ["Short", "Medium", "Long"]


def test_generate_schedule_returns_tasks_in_chronological_order() -> None:
	owner = Owner(name="Jordan", time_available_minutes=45)
	pet = Pet(name="Mochi", species="dog")
	tasks = [
		Task(description="Daily feed", time_minutes=5, frequency="daily", pet_name="Mochi"),
		Task(description="Walk", time_minutes=20, frequency="daily", pet_name="Mochi"),
		Task(description="Weekly brush", time_minutes=10, frequency="weekly", pet_name="Mochi"),
	]

	generator = DailyScheduleGenerator()
	plan = generator.generate_schedule(owner, pet, tasks)

	start_minutes = [item.start_minute for item in plan.scheduled]
	assert start_minutes == sorted(start_minutes)
	assert [item.task_title for item in plan.scheduled] == [
		"Daily feed",
		"Walk",
		"Weekly brush",
	]


def test_filter_tasks_by_pet_and_status() -> None:
	owner = Owner(name="Jordan", time_available_minutes=60)
	dog = Pet(name="Mochi", species="dog")
	cat = Pet(name="Luna", species="cat")
	owner.add_pet(dog)
	owner.add_pet(cat)

	dog_task = Task(description="Walk", time_minutes=20, frequency="daily")
	cat_task = Task(description="Litter", time_minutes=10, frequency="daily")
	dog.add_task(dog_task)
	cat.add_task(cat_task)
	dog_task.mark_complete()

	scheduler = Scheduler()
	filtered = scheduler.filter_tasks(owner, pet_name="Mochi", completed=True)

	assert len(filtered) == 1
	assert filtered[0].description == "Walk"


def test_recurring_task_due_logic() -> None:
	scheduler = Scheduler()
	weekly_task = Task(
		description="Grooming",
		time_minutes=30,
		frequency="weekly",
		last_completed_day=2,
	)

	assert scheduler.is_task_due(weekly_task, day_index=6) is False
	assert scheduler.is_task_due(weekly_task, day_index=9) is True


def test_detect_conflicts_when_time_exceeds_availability() -> None:
	scheduler = Scheduler()
	tasks = [
		Task(description="Walk", time_minutes=40, frequency="daily", pet_name="Mochi"),
		Task(description="Feed", time_minutes=30, frequency="daily", pet_name="Mochi"),
	]

	conflicts = scheduler.detect_conflicts(tasks, available_minutes=60)

	assert any("exceeds available time" in item for item in conflicts)


def test_mark_daily_task_complete_creates_next_occurrence() -> None:
	owner = Owner(name="Jordan", time_available_minutes=60)
	pet = Pet(name="Mochi", species="dog")
	owner.add_pet(pet)
	original = Task(description="Walk", time_minutes=20, frequency="daily")
	pet.add_task(original)

	scheduler = Scheduler()
	base_date = date(2026, 3, 25)
	spawned = scheduler.mark_task_complete(owner, original.id, current_day=3, current_date=base_date)

	assert spawned is not None
	assert original.completed is True
	assert len(pet.tasks) == 2
	assert spawned.id != original.id
	assert spawned.frequency == "daily"
	assert scheduler.is_task_due(spawned, current_date=base_date) is False
	assert scheduler.is_task_due(spawned, current_date=base_date + timedelta(days=1)) is True


def test_mark_weekly_task_complete_creates_next_occurrence() -> None:
	owner = Owner(name="Jordan", time_available_minutes=60)
	pet = Pet(name="Luna", species="cat")
	owner.add_pet(pet)
	original = Task(description="Deep clean", time_minutes=30, frequency="weekly")
	pet.add_task(original)

	scheduler = Scheduler()
	base_date = date(2026, 3, 25)
	spawned = scheduler.mark_task_complete(owner, original.id, current_day=5, current_date=base_date)

	assert spawned is not None
	assert original.completed is True
	assert len(pet.tasks) == 2
	assert spawned.frequency == "weekly"
	assert scheduler.is_task_due(spawned, current_date=base_date + timedelta(days=6)) is False
	assert scheduler.is_task_due(spawned, current_date=base_date + timedelta(days=7)) is True


def test_mark_daily_task_complete_sets_due_date_with_timedelta() -> None:
	owner = Owner(name="Jordan", time_available_minutes=60)
	pet = Pet(name="Mochi", species="dog")
	owner.add_pet(pet)
	original = Task(description="Water bowl", time_minutes=5, frequency="daily")
	pet.add_task(original)

	scheduler = Scheduler()
	base_date = date(2026, 3, 25)
	spawned = scheduler.mark_task_complete(owner, original.id, current_date=base_date)

	assert spawned is not None
	assert spawned.due_date == base_date + timedelta(days=1)


def test_mark_weekly_task_complete_sets_due_date_with_timedelta() -> None:
	owner = Owner(name="Jordan", time_available_minutes=60)
	pet = Pet(name="Luna", species="cat")
	owner.add_pet(pet)
	original = Task(description="Nail trim", time_minutes=15, frequency="weekly")
	pet.add_task(original)

	scheduler = Scheduler()
	base_date = date(2026, 3, 25)
	spawned = scheduler.mark_task_complete(owner, original.id, current_date=base_date)

	assert spawned is not None
	assert spawned.due_date == base_date + timedelta(days=7)


def test_detect_same_pet_preferred_time_conflicts() -> None:
	"""Test detection of overlapping preferred start times for the same pet."""
	scheduler = Scheduler()
	tasks = [
		Task(description="Morning meds", time_minutes=5, frequency="daily", pet_name="Mochi", preferred_start_minute=0),
		Task(description="Breakfast", time_minutes=10, frequency="daily", pet_name="Mochi", preferred_start_minute=3),
	]

	conflicts = scheduler.detect_conflicts(tasks, available_minutes=60)

	assert any("Preferred-time overlap" in item and "Mochi" in item for item in conflicts)


def test_detect_different_pet_preferred_time_conflicts() -> None:
	"""Test detection of overlapping preferred start times for different pets."""
	scheduler = Scheduler()
	tasks = [
		Task(description="Mochi feeding", time_minutes=10, frequency="daily", pet_name="Mochi", preferred_start_minute=10),
		Task(description="Luna feeding", time_minutes=15, frequency="daily", pet_name="Luna", preferred_start_minute=15),
	]

	conflicts = scheduler.detect_conflicts(tasks, available_minutes=120)

	# Check for cross-pet time conflict
	assert any("Time conflict across different pets" in item for item in conflicts)


def test_detect_scheduled_task_time_overlaps_same_pet() -> None:
	"""Test detection of overlapping scheduled times for the same pet."""
	scheduler = Scheduler()
	scheduled_tasks = [
		ScheduledTask(task_id="1", task_title="Walk", start_minute=0, end_minute=20, reason="Morning"),
		ScheduledTask(task_id="2", task_title="Play", start_minute=15, end_minute=30, reason="Afternoon"),
	]

	conflicts = scheduler.detect_scheduled_time_conflicts(scheduled_tasks)

	assert len(conflicts) > 0
	assert any("Time conflict detected" in item for item in conflicts)
	assert any("Walk" in item and "Play" in item for item in conflicts)


def test_detect_scheduled_task_time_overlaps_different_pets() -> None:
	"""Test detection of overlapping scheduled times for different pets."""
	scheduler = Scheduler()
	scheduled_tasks = [
		ScheduledTask(task_id="1", task_title="Mochi: Walk", start_minute=10, end_minute=30, reason="Mochi"),
		ScheduledTask(task_id="2", task_title="Luna: Groom", start_minute=25, end_minute=45, reason="Luna"),
	]

	conflicts = scheduler.detect_scheduled_time_conflicts(scheduled_tasks)

	assert len(conflicts) > 0
	assert any("Time conflict detected" in item for item in conflicts)


def test_no_overlap_when_tasks_are_sequential() -> None:
	"""Test that sequential tasks don't create overlap conflicts."""
	scheduler = Scheduler()
	scheduled_tasks = [
		ScheduledTask(task_id="1", task_title="Walk", start_minute=0, end_minute=20, reason="Morning"),
		ScheduledTask(task_id="2", task_title="Feeding", start_minute=20, end_minute=25, reason="Afternoon"),
	]

	conflicts = scheduler.detect_scheduled_time_conflicts(scheduled_tasks)

	assert len(conflicts) == 0


def test_has_time_overlap_helper() -> None:
	"""Test the time overlap helper method."""
	scheduler = Scheduler()
	
	# Overlapping windows
	assert scheduler._has_time_overlap(0, 10, 5, 15) is True
	assert scheduler._has_time_overlap(5, 15, 0, 10) is True
	
	# Non-overlapping windows
	assert scheduler._has_time_overlap(0, 10, 10, 20) is False
	assert scheduler._has_time_overlap(10, 20, 0, 10) is False
	
	# Identical windows
	assert scheduler._has_time_overlap(10, 20, 10, 20) is True
	
	# One contains the other
	assert scheduler._has_time_overlap(0, 30, 10, 20) is True


# ====== LIGHTWEIGHT CONFLICT DETECTION TESTS ======

def test_lightweight_safe_has_time_overlap_with_none() -> None:
	"""Test safe overlap checking handles None values gracefully."""
	# Should not crash and return False for None values
	assert LightweightConflictDetector.safe_has_time_overlap(None, 10, 5, 15) is False
	assert LightweightConflictDetector.safe_has_time_overlap(0, None, 5, 15) is False
	assert LightweightConflictDetector.safe_has_time_overlap(0, 10, None, 15) is False
	assert LightweightConflictDetector.safe_has_time_overlap(0, 10, 5, None) is False


def test_lightweight_validate_task_duration() -> None:
	"""Test task duration validation returns appropriate warnings."""
	# Valid task duration
	valid_task = Task(description="Walk", time_minutes=20, frequency="daily")
	assert LightweightConflictDetector.validate_task_duration(valid_task) is None

	# Invalid: zero duration
	zero_task = Task(description="Task", time_minutes=0, frequency="daily")
	warning = LightweightConflictDetector.validate_task_duration(zero_task)
	assert warning is not None
	assert warning.level == "warning"

	# Invalid: negative duration
	negative_task = Task(description="Task", time_minutes=-5, frequency="daily")
	warning = LightweightConflictDetector.validate_task_duration(negative_task)
	assert warning is not None
	assert warning.level == "warning"


def test_lightweight_check_time_budget() -> None:
	"""Test time budget checking returns appropriate warnings."""
	tasks = [
		Task(description="Walk", time_minutes=40, frequency="daily", pet_name="Mochi"),
		Task(description="Feed", time_minutes=30, frequency="daily", pet_name="Mochi"),
	]

	# Over budget
	warning = LightweightConflictDetector.check_time_budget(tasks, available_minutes=60)
	assert warning is not None
	assert warning.level == "warning"
	assert "exceeds available time" in warning.message

	# Under budget - no warning
	warning = LightweightConflictDetector.check_time_budget(tasks, available_minutes=100)
	assert warning is None


def test_lightweight_check_preferred_overlaps() -> None:
	"""Test preferred time overlap detection returns warnings."""
	tasks = [
		Task(
			description="Meds",
			time_minutes=5,
			frequency="daily",
			pet_name="Mochi",
			preferred_start_minute=0,
		),
		Task(
			description="Breakfast",
			time_minutes=10,
			frequency="daily",
			pet_name="Mochi",
			preferred_start_minute=3,
		),
	]

	warnings = LightweightConflictDetector.check_preferred_time_overlaps(tasks)
	assert len(warnings) > 0
	assert warnings[0].level == "warning"
	assert "Mochi" in warnings[0].message


def test_lightweight_check_scheduled_overlaps() -> None:
	"""Test scheduled task overlap detection returns warnings."""
	scheduled = [
		ScheduledTask(task_id="1", task_title="Walk", start_minute=0, end_minute=20, reason=""),
		ScheduledTask(task_id="2", task_title="Play", start_minute=15, end_minute=30, reason=""),
	]

	warnings = LightweightConflictDetector.check_scheduled_overlaps(scheduled)
	assert len(warnings) > 0
	assert warnings[0].level == "warning"
	assert "Walk" in warnings[0].message
	assert "Play" in warnings[0].message


def test_lightweight_detect_all_conflicts_safe() -> None:
	"""Test comprehensive lightweight detection never crashes."""
	owner = Owner(name="Test", time_available_minutes=60)
	pet = Pet(name="Mochi", species="dog")
	owner.add_pet(pet)
	pet.add_task(Task(description="Walk", time_minutes=40, frequency="daily"))
	pet.add_task(Task(description="Feed", time_minutes=30, frequency="daily"))

	# Should not crash even with problematic data
	warnings = LightweightConflictDetector.detect_all_conflicts(
		tasks=pet.list_tasks(),
		available_minutes=60,
	)
	assert isinstance(warnings, list)
	assert all(isinstance(w, ConflictWarning) for w in warnings)


def test_conflict_warning_str_representation() -> None:
	"""Test ConflictWarning string representation."""
	warning = ConflictWarning(
		level="warning",
		message="Test conflict",
		affected_tasks=["1", "2"],
		pet_names=["Mochi"],
	)

	result = str(warning)
	assert "WARNING" in result
	assert "Test conflict" in result
	assert "⚠️" in result


def test_scheduler_detect_conflicts_lightweight_no_crash() -> None:
	"""Test Scheduler lightweight conflict detection never crashes."""
	owner = Owner(name="Test", time_available_minutes=60)
	pet = Pet(name="Mochi", species="dog")
	owner.add_pet(pet)
	pet.add_task(Task(description="Walk", time_minutes=20, frequency="daily"))

	scheduler = Scheduler()
	
	# Should not crash, should return ConflictWarning objects
	warnings = scheduler.detect_conflicts_lightweight(owner)
	assert isinstance(warnings, list)
	assert all(isinstance(w, ConflictWarning) for w in warnings)


def test_scheduler_detect_conflicts_lightweight_with_scheduled_tasks() -> None:
	"""Test Scheduler lightweight conflict detection with scheduled tasks."""
	owner = Owner(name="Test", time_available_minutes=120)
	pet = Pet(name="Mochi", species="dog")
	owner.add_pet(pet)
	pet.add_task(Task(description="Walk", time_minutes=20, frequency="daily"))
	pet.add_task(Task(description="Feed", time_minutes=10, frequency="daily"))

	scheduled = [
		ScheduledTask(task_id="1", task_title="Walk", start_minute=0, end_minute=20, reason=""),
		ScheduledTask(task_id="2", task_title="Play", start_minute=15, end_minute=30, reason=""),
	]

	scheduler = Scheduler()
	warnings = scheduler.detect_conflicts_lightweight(owner, scheduled_tasks=scheduled)
	
	assert isinstance(warnings, list)
	assert all(isinstance(w, ConflictWarning) for w in warnings)
	# Should detect the overlap
	assert any("overlap" in w.message.lower() for w in warnings)
	assert scheduler._has_time_overlap(10, 20, 0, 30) is True


def test_build_daily_schedule_happy_path_orders_by_frequency_then_duration() -> None:
	owner = Owner(name="Jordan", time_available_minutes=60)
	pet = Pet(name="Mochi", species="dog")
	owner.add_pet(pet)

	pet.add_task(Task(description="Weekly grooming", time_minutes=10, frequency="weekly"))
	pet.add_task(Task(description="Daily walk", time_minutes=20, frequency="daily"))
	pet.add_task(Task(description="Daily feed", time_minutes=5, frequency="daily"))

	scheduler = Scheduler()
	plan = scheduler.build_daily_schedule(owner)

	assert [task.description for task in plan["scheduled"]] == [
		"Daily feed",
		"Daily walk",
		"Weekly grooming",
	]
	assert plan["deferred"] == []


def test_build_daily_schedule_for_pet_with_no_tasks_is_empty() -> None:
	owner = Owner(name="Jordan", time_available_minutes=45)
	pet = Pet(name="Mochi", species="dog")
	owner.add_pet(pet)

	scheduler = Scheduler()
	plan = scheduler.build_daily_schedule(owner)

	assert plan["scheduled"] == []
	assert plan["deferred"] == []
	assert plan["conflicts"] == []


def test_build_daily_schedule_with_zero_available_time_defers_all() -> None:
	owner = Owner(name="Jordan", time_available_minutes=0)
	pet = Pet(name="Mochi", species="dog")
	owner.add_pet(pet)
	pet.add_task(Task(description="Walk", time_minutes=20, frequency="daily", pet_name="Mochi"))

	scheduler = Scheduler()
	plan = scheduler.build_daily_schedule(owner)

	assert plan["scheduled"] == []
	assert len(plan["deferred"]) == 1
	assert any("exceeds available time" in item for item in plan["conflicts"])


def test_detect_scheduled_time_conflicts_with_identical_windows() -> None:
	scheduler = Scheduler()
	scheduled_tasks = [
		ScheduledTask(task_id="1", task_title="Walk", start_minute=10, end_minute=20, reason=""),
		ScheduledTask(task_id="2", task_title="Feed", start_minute=10, end_minute=20, reason=""),
	]

	conflicts = scheduler.detect_scheduled_time_conflicts(scheduled_tasks)

	assert len(conflicts) > 0
	assert any("Time conflict detected" in item for item in conflicts)


def test_is_task_due_unknown_frequency_defaults_to_not_completed() -> None:
	scheduler = Scheduler()
	unknown_frequency_task = Task(description="Custom", time_minutes=5, frequency="yearly")

	assert scheduler.is_task_due(unknown_frequency_task) is True
	unknown_frequency_task.mark_complete()
	assert scheduler.is_task_due(unknown_frequency_task) is False


def test_mark_task_complete_twice_does_not_spawn_duplicate_occurrence() -> None:
	owner = Owner(name="Jordan", time_available_minutes=60)
	pet = Pet(name="Mochi", species="dog")
	owner.add_pet(pet)
	original = Task(description="Walk", time_minutes=20, frequency="daily")
	pet.add_task(original)

	scheduler = Scheduler()
	first_spawned = scheduler.mark_task_complete(owner, original.id)
	second_spawned = scheduler.mark_task_complete(owner, original.id)

	assert first_spawned is not None
	assert second_spawned is None
	assert len(pet.tasks) == 2


def test_mark_task_complete_raises_for_missing_task_id() -> None:
	owner = Owner(name="Jordan", time_available_minutes=60)
	pet = Pet(name="Mochi", species="dog")
	owner.add_pet(pet)

	scheduler = Scheduler()
	with pytest.raises(ValueError, match="not found"):
		scheduler.mark_task_complete(owner, "missing-id")

