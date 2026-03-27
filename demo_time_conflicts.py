"""Demonstration of the enhanced Scheduler time conflict detection."""

from pawpal_system import Owner, Pet, Scheduler, Task, ScheduledTask


def demo_same_pet_time_conflicts():
	"""Demo: Detect overlapping preferred start times for the same pet."""
	print("\n" + "="*70)
	print("DEMO 1: Same Pet - Overlapping Preferred Start Times")
	print("="*70)
	
	scheduler = Scheduler()
	
	# Create tasks for Mochi with overlapping preferred times
	tasks = [
		Task(
			description="Morning meds",
			time_minutes=5,
			frequency="daily",
			pet_name="Mochi",
			preferred_start_minute=0
		),
		Task(
			description="Breakfast",
			time_minutes=10,
			frequency="daily",
			pet_name="Mochi",
			preferred_start_minute=3  # Overlaps with meds (0-5)
		),
	]
	
	print("\nTasks for Mochi:")
	for task in tasks:
		end_time = task.preferred_start_minute + task.time_minutes if task.preferred_start_minute else "N/A"
		print(f"  - {task.description} ({task.time_minutes} min, preferred: {task.preferred_start_minute}-{end_time} min)")
	
	conflicts = scheduler.detect_conflicts(tasks, available_minutes=60)
	
	print("\nDetected conflicts:")
	if conflicts:
		for conflict in conflicts:
			print(f"  ⚠️  {conflict}")
	else:
		print("  No conflicts detected")


def demo_different_pets_time_conflicts():
	"""Demo: Detect overlapping preferred start times for different pets."""
	print("\n" + "="*70)
	print("DEMO 2: Different Pets - Overlapping Preferred Start Times")
	print("="*70)
	
	scheduler = Scheduler()
	
	# Create tasks for different pets with overlapping preferred times
	tasks = [
		Task(
			description="Mochi feeding",
			time_minutes=10,
			frequency="daily",
			pet_name="Mochi",
			preferred_start_minute=10
		),
		Task(
			description="Luna feeding",
			time_minutes=15,
			frequency="daily",
			pet_name="Luna",
			preferred_start_minute=15  # Overlaps with Mochi (10-20)
		),
	]
	
	print("\nTasks for multiple pets:")
	for task in tasks:
		end_time = task.preferred_start_minute + task.time_minutes if task.preferred_start_minute else "N/A"
		print(f"  - {task.pet_name}: {task.description} ({task.time_minutes} min, preferred: {task.preferred_start_minute}-{end_time} min)")
	
	conflicts = scheduler.detect_conflicts(tasks, available_minutes=120)
	
	print("\nDetected conflicts:")
	if conflicts:
		for conflict in conflicts:
			print(f"  ⚠️  {conflict}")
	else:
		print("  No conflicts detected")


def demo_scheduled_task_overlaps():
	"""Demo: Detect overlapping scheduled time windows."""
	print("\n" + "="*70)
	print("DEMO 3: Scheduled Tasks - Overlapping Time Windows")
	print("="*70)
	
	scheduler = Scheduler()
	
	# Create already-scheduled tasks with overlapping times
	scheduled_tasks = [
		ScheduledTask(
			task_id="1",
			task_title="Mochi: Morning walk",
			start_minute=0,
			end_minute=20,
			reason="Morning routine"
		),
		ScheduledTask(
			task_id="2",
			task_title="Luna: Feeding",
			start_minute=15,
			end_minute=30,
			reason="Daily feeding"
		),
		ScheduledTask(
			task_id="3",
			task_title="Mochi: Playtime",
			start_minute=30,
			end_minute=45,
			reason="Exercise"
		),
	]
	
	print("\nScheduled tasks:")
	for task in scheduled_tasks:
		print(f"  - {task.task_title} ({task.start_minute}-{task.end_minute} min)")
	
	conflicts = scheduler.detect_scheduled_time_conflicts(scheduled_tasks)
	
	print("\nDetected time conflicts:")
	if conflicts:
		for conflict in conflicts:
			print(f"  ⚠️  {conflict}")
	else:
		print("  No overlaps detected")


def demo_sequential_tasks_no_conflict():
	"""Demo: Sequential tasks do NOT create conflicts."""
	print("\n" + "="*70)
	print("DEMO 4: Sequential Tasks - No Conflicts (Expected)")
	print("="*70)
	
	scheduler = Scheduler()
	
	# Create sequential tasks with no overlap
	scheduled_tasks = [
		ScheduledTask(
			task_id="1",
			task_title="Mochi: Morning walk",
			start_minute=0,
			end_minute=20,
			reason="Morning routine"
		),
		ScheduledTask(
			task_id="2",
			task_title="Mochi: Feeding",
			start_minute=20,
			end_minute=25,
			reason="Feeding time"
		),
		ScheduledTask(
			task_id="3",
			task_title="Luna: Grooming",
			start_minute=25,
			end_minute=40,
			reason="Grooming"
		),
	]
	
	print("\nScheduled tasks:")
	for task in scheduled_tasks:
		print(f"  - {task.task_title} ({task.start_minute}-{task.end_minute} min)")
	
	conflicts = scheduler.detect_scheduled_time_conflicts(scheduled_tasks)
	
	print("\nDetected time conflicts:")
	if conflicts:
		for conflict in conflicts:
			print(f"  ⚠️  {conflict}")
	else:
		print("  ✓ No overlaps detected - tasks are properly sequenced!")


def demo_full_schedule_with_conflicts():
	"""Demo: Full daily schedule generation with conflict detection."""
	print("\n" + "="*70)
	print("DEMO 5: Full Daily Schedule with Conflict Detection")
	print("="*70)
	
	# Create owner and pets
	owner = Owner(name="Alex", time_available_minutes=120)
	mochi = Pet(name="Mochi", species="dog")
	luna = Pet(name="Luna", species="cat")
	owner.add_pet(mochi)
	owner.add_pet(luna)
	
	# Add tasks for Mochi
	mochi.add_task(Task(description="Morning walk", time_minutes=20, frequency="daily", preferred_start_minute=0))
	mochi.add_task(Task(description="Feeding", time_minutes=10, frequency="daily", preferred_start_minute=50))
	mochi.add_task(Task(description="Play time", time_minutes=15, frequency="daily", preferred_start_minute=15))
	
	# Add tasks for Luna
	luna.add_task(Task(description="Feeding", time_minutes=10, frequency="daily", preferred_start_minute=10))
	luna.add_task(Task(description="Grooming", time_minutes=20, frequency="daily", preferred_start_minute=70))
	luna.add_task(Task(description="Playtime", time_minutes=15, frequency="daily", preferred_start_minute=85))
	
	scheduler = Scheduler()
	schedule = scheduler.build_daily_schedule(owner)
	
	print(f"\nOwner: {owner.name} | Available time: {owner.time_available_minutes} minutes")
	print(f"\nScheduled tasks ({len(schedule['scheduled'])} total):")
	for task in schedule['scheduled']:
		print(f"  - {task.pet_name}: {task.description} ({task.time_minutes} min)")
	
	if schedule['deferred']:
		print(f"\nDeferred tasks ({len(schedule['deferred'])} total):")
		for task in schedule['deferred']:
			print(f"  - {task.pet_name}: {task.description} ({task.time_minutes} min)")
	
	if schedule['conflicts']:
		print(f"\nDetected conflicts ({len(schedule['conflicts'])} total):")
		for conflict in schedule['conflicts']:
			print(f"  ⚠️  {conflict}")
	else:
		print("\n✓ No scheduling conflicts detected!")


if __name__ == "__main__":
	print("\n🐾 PawPal Scheduler - Time Conflict Detection Demonstrations 🐾")
	
	demo_same_pet_time_conflicts()
	demo_different_pets_time_conflicts()
	demo_scheduled_task_overlaps()
	demo_sequential_tasks_no_conflict()
	demo_full_schedule_with_conflicts()
	
	print("\n" + "="*70)
	print("All demonstrations completed!")
	print("="*70)
