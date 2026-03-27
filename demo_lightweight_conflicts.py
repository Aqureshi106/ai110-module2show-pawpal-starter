"""Demonstration of the Lightweight Conflict Detection Strategy.

This script shows how the new lightweight conflict detection returns
warning messages instead of crashing the program.
"""

from pawpal_system import (
	Owner, Pet, Scheduler, Task, ScheduledTask,
	ConflictWarning, LightweightConflictDetector
)


def print_warnings(warnings: list[ConflictWarning]) -> None:
	"""Pretty print warning messages."""
	if not warnings:
		print("  ✓ No warnings detected!")
		return
	for warning in warnings:
		print(f"  {warning}")
		if warning.affected_tasks:
			print(f"    Affected tasks: {', '.join(warning.affected_tasks)}")


def demo_safe_handling_of_none_values():
	"""Demo: Lightweight detector handles None values gracefully."""
	print("\n" + "="*70)
	print("DEMO 1: Graceful Handling of None/Invalid Data")
	print("="*70)
	print("\nTesting safe_has_time_overlap with None values (won't crash):")
	
	result = LightweightConflictDetector.safe_has_time_overlap(None, 10, 5, 15)
	print(f"  safe_has_time_overlap(None, 10, 5, 15) = {result} (safely handled)")
	
	result = LightweightConflictDetector.safe_has_time_overlap(0, None, 5, 15)
	print(f"  safe_has_time_overlap(0, None, 5, 15) = {result} (safely handled)")
	
	result = LightweightConflictDetector.safe_has_time_overlap(-5, 10, 5, 15)
	print(f"  safe_has_time_overlap(-5, 10, 5, 15) = {result} (safely handled)")
	
	print("\n✓ No crashes! All invalid data handled gracefully.")


def demo_task_duration_validation():
	"""Demo: Task duration validation returns warnings."""
	print("\n" + "="*70)
	print("DEMO 2: Task Duration Validation")
	print("="*70)
	
	print("\nValidating tasks with different durations:")
	
	tasks = [
		Task(description="Valid task", time_minutes=20, frequency="daily"),
		Task(description="Zero duration", time_minutes=0, frequency="daily"),
		Task(description="Negative duration", time_minutes=-5, frequency="daily"),
	]
	
	for task in tasks:
		warning = LightweightConflictDetector.validate_task_duration(task)
		if warning:
			print(f"  {warning}")
		else:
			print(f"  ✓ {task.description} ({task.time_minutes} min) - valid")


def demo_time_budget_checking():
	"""Demo: Time budget checking without crashing."""
	print("\n" + "="*70)
	print("DEMO 3: Time Budget Checking")
	print("="*70)
	
	print("\nChecking if tasks fit within available time:")
	
	tasks = [
		Task(description="Morning walk", time_minutes=30, frequency="daily", pet_name="Mochi"),
		Task(description="Feeding", time_minutes=25, frequency="daily", pet_name="Mochi"),
		Task(description="Playtime", time_minutes=25, frequency="daily", pet_name="Mochi"),
	]
	
	total = sum(t.time_minutes for t in tasks)
	print(f"  Total task time: {total} minutes")
	
	available = 60
	warning = LightweightConflictDetector.check_time_budget(tasks, available_minutes=available)
	if warning:
		print(f"  {warning}")
	else:
		print(f"  ✓ Fits within {available} minutes available")
	
	print(f"\n  With 100 minutes available:")
	warning = LightweightConflictDetector.check_time_budget(tasks, available_minutes=100)
	if warning:
		print(f"  {warning}")
	else:
		print(f"  ✓ Fits comfortably!")


def demo_comprehensive_lightweight_detection():
	"""Demo: Comprehensive lightweight detection with edge cases."""
	print("\n" + "="*70)
	print("DEMO 4: Comprehensive Lightweight Conflict Detection")
	print("="*70)
	
	print("\nScenario: Owner with two pets and various scheduling issues")
	
	owner = Owner(name="Alex", time_available_minutes=90)
	mochi = Pet(name="Mochi", species="dog")
	luna = Pet(name="Luna", species="cat")
	owner.add_pet(mochi)
	owner.add_pet(luna)
	
	# Add tasks with various issues
	mochi.add_task(Task(
		description="Morning walk",
		time_minutes=30,
		frequency="daily",
		preferred_start_minute=0
	))
	mochi.add_task(Task(
		description="Playtime",
		time_minutes=25,
		frequency="daily",
		preferred_start_minute=15  # Overlaps with walk
	))
	luna.add_task(Task(
		description="Feeding",
		time_minutes=20,
		frequency="daily",
		preferred_start_minute=20
	))
	luna.add_task(Task(
		description="Grooming",
		time_minutes=25,
		frequency="daily"
	))
	
	print("\nRunning lightweight conflict detection...")
	scheduler = Scheduler()
	warnings = scheduler.detect_conflicts_lightweight(owner)
	
	print(f"\nDetected {len(warnings)} warning(s):")
	print_warnings(warnings)


def demo_no_crash_with_bad_data():
	"""Demo: Lightweight detection never crashes, even with bad data."""
	print("\n" + "="*70)
	print("DEMO 5: Resilience Test - Bad Data Doesn't Crash")
	print("="*70)
	
	print("\nCreating problematic tasks and scheduling:")
	
	owner = Owner(name="Test", time_available_minutes=60)
	pet = Pet(name="TestPet", species="test")
	owner.add_pet(pet)
	
	# Add tasks with issues
	pet.add_task(Task(description="Task1", time_minutes=50, frequency="daily"))
	pet.add_task(Task(description="Task2", time_minutes=50, frequency="daily"))
	pet.add_task(Task(description="Task3", time_minutes=50, frequency="daily"))
	
	# Create scheduled tasks too
	scheduled = [
		ScheduledTask(task_id="1", task_title="A", start_minute=0, end_minute=30, reason=""),
		ScheduledTask(task_id="2", task_title="B", start_minute=20, end_minute=50, reason=""),
		ScheduledTask(task_id="3", task_title="C", start_minute=40, end_minute=70, reason=""),
	]
	
	print("  - Total task time: 150 minutes")
	print("  - Available time: 60 minutes")
	print("  - Multiple overlapping scheduled tasks")
	
	scheduler = Scheduler()
	
	print("\nRunning lightweight detection (won't crash)...")
	try:
		warnings = scheduler.detect_conflicts_lightweight(owner, scheduled_tasks=scheduled)
		print(f"✓ Success! Got {len(warnings)} warning(s) without crashing:")
		print_warnings(warnings)
	except Exception as e:
		print(f"✗ Unexpected crash: {e}")


def demo_warning_levels():
	"""Demo: Different warning levels."""
	print("\n" + "="*70)
	print("DEMO 6: Warning Levels")
	print("="*70)
	
	print("\nDifferent severity levels for conflicts:")
	
	warnings = [
		ConflictWarning(level="info", message="Recurring task created from completion"),
		ConflictWarning(level="warning", message="Task time exceeds available budget by 30 min"),
		ConflictWarning(level="critical", message="Invalid task duration: cannot schedule"),
	]
	
	for warning in warnings:
		print(f"  {warning}")


def demo_real_world_scenario():
	"""Demo: Real-world scenario with actual pets and tasks."""
	print("\n" + "="*70)
	print("DEMO 7: Real-World Scenario")
	print("="*70)
	
	print("\nFamily with multiple pets and a busy schedule:")
	
	# Create realistic scenario
	owner = Owner(name="Jordan", time_available_minutes=120)
	dog = Pet(name="Max", species="dog")
	cat = Pet(name="Whiskers", species="cat")
	owner.add_pet(dog)
	owner.add_pet(cat)
	
	# Dog tasks
	dog.add_task(Task(
		description="Morning walk",
		time_minutes=30,
		frequency="daily",
		preferred_start_minute=0
	))
	dog.add_task(Task(
		description="Evening walk",
		time_minutes=30,
		frequency="daily",
		preferred_start_minute=60
	))
	dog.add_task(Task(
		description="Feeding",
		time_minutes=15,
		frequency="daily",
		preferred_start_minute=35
	))
	
	# Cat tasks
	cat.add_task(Task(
		description="Feeding",
		time_minutes=10,
		frequency="daily",
		preferred_start_minute=35  # Overlaps with dog feeding
	))
	cat.add_task(Task(
		description="Play session",
		time_minutes=20,
		frequency="daily"
	))
	cat.add_task(Task(
		description="Litter box cleaning",
		time_minutes=10,
		frequency="daily"
	))
	
	print(f"\nOwner: {owner.name}")
	print(f"Available time: {owner.time_available_minutes} minutes")
	print(f"Pets: {len(owner.pets)}")
	for pet in owner.pets:
		print(f"  - {pet.name}: {len(pet.tasks)} tasks")
	
	scheduler = Scheduler()
	warnings = scheduler.detect_conflicts_lightweight(owner)
	
	print(f"\nRunning lightweight conflict detection...")
	print(f"Found {len(warnings)} potential conflicts/warnings:\n")
	print_warnings(warnings)
	
	print(f"\n✓ Program continues smoothly despite conflicts!")
	print(f"  Warnings inform the user without crashing the system.")


if __name__ == "__main__":
	print("\n🐾 LIGHTWEIGHT CONFLICT DETECTION STRATEGY 🐾")
	print("Returns Warnings Instead of Crashing")
	
	demo_safe_handling_of_none_values()
	demo_task_duration_validation()
	demo_time_budget_checking()
	demo_comprehensive_lightweight_detection()
	demo_no_crash_with_bad_data()
	demo_warning_levels()
	demo_real_world_scenario()
	
	print("\n" + "="*70)
	print("Key Benefits of Lightweight Strategy:")
	print("="*70)
	print("""
	✓ Never crashes - all exceptions handled gracefully
	✓ Returns ConflictWarning objects with detailed info
	✓ Handles None/invalid data without issues
	✓ Works with partially formed data
	✓ Provides structured warnings for UI integration
	✓ Different severity levels (info, warning, critical)
	✓ Tracks affected tasks and pets
	✓ Safe for production use
	""")
	print("="*70)
