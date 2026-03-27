from pawpal_system import Owner, Pet, Scheduler, Task


def print_todays_schedule(owner: Owner, scheduler: Scheduler) -> None:
	print("Today's Schedule")
	print("=" * 16)

	plan = scheduler.build_daily_schedule(owner)
	organized_tasks = plan["scheduled"]
	deferred_tasks = plan["deferred"]
	conflicts = plan["conflicts"]
	current_minute = 0

	for task in organized_tasks:
		start = current_minute
		end = current_minute + task.time_minutes
		print(
			f"- {start:02d}-{end:02d} min | {task.pet_name}: {task.description} "
			f"({task.time_minutes} min, {task.frequency})"
		)
		current_minute = end

	for task in deferred_tasks:
		print(f"- DEFERRED: {task.description} ({task.time_minutes} min) for {task.pet_name}")

	if conflicts:
		print("\nConflicts detected:")
		for item in conflicts:
			print(f"- {item}")


def print_lightweight_conflict_detection_demo(owner: Owner, scheduler: Scheduler) -> None:
	"""Demonstrate lightweight conflict detection with overlapping task times."""
	print("\n" + "=" * 70)
	print("LIGHTWEIGHT CONFLICT DETECTION - Tasks Scheduled at Same Time")
	print("=" * 70)

	print("\nScenario: Two pets with tasks scheduled at the same time")
	print(f"Owner: {owner.name} | Available time: {owner.time_available_minutes} minutes")
	print(f"\nPets and their tasks (with preferred start times):")
	
	for pet in owner.pets:
		print(f"\n  {pet.name}:")
		for task in pet.tasks:
			if task.preferred_start_minute is not None:
				end_time = task.preferred_start_minute + task.time_minutes
				print(f"    - {task.description}: {task.preferred_start_minute}-{end_time} min ({task.time_minutes} min)")
			else:
				print(f"    - {task.description}: (no preferred time) ({task.time_minutes} min)")

	print("\n" + "-" * 70)
	print("Running Lightweight Conflict Detection...")
	print("-" * 70)

	warnings = scheduler.detect_conflicts_lightweight(owner)

	if not warnings:
		print("✓ No conflicts detected!")
	else:
		print(f"\n⚠️  WARNINGS DETECTED ({len(warnings)} total):\n")
		for i, warning in enumerate(warnings, 1):
			print(f"{i}. {warning}")
			if warning.affected_tasks:
				print(f"   └─ Affected task IDs: {', '.join(warning.affected_tasks)}")
			if warning.pet_names:
				print(f"   └─ Affected pets: {', '.join(warning.pet_names)}")

	print("\n✓ System continues safely - warnings handled gracefully!")


def print_sorting_and_filtering_demo(owner: Owner, scheduler: Scheduler) -> None:
	print("\nSorting + Filtering Demo")
	print("=" * 24)

	all_tasks = owner.get_all_tasks()
	print("Added order:")
	for task in all_tasks:
		status = "done" if task.completed else "pending"
		print(f"- {task.pet_name}: {task.description} ({task.time_minutes} min, {status})")

	print("\nSorted by time (shortest first):")
	for task in scheduler.sort_by_time(all_tasks, ascending=True):
		print(f"- {task.pet_name}: {task.description} ({task.time_minutes} min)")

	print("\nFiltered by pet='Mochi':")
	for task in scheduler.filter_tasks(owner, pet_name="Mochi"):
		status = "done" if task.completed else "pending"
		print(f"- {task.description} ({task.time_minutes} min, {status})")

	print("\nFiltered by completed=False:")
	for task in scheduler.filter_tasks(owner, completed=False):
		print(f"- {task.pet_name}: {task.description} ({task.time_minutes} min)")


def main() -> None:
	owner = Owner(name="Jordan", time_available_minutes=60, preferences=["morning"])

	dog = Pet(name="Mochi", species="dog")
	cat = Pet(name="Luna", species="cat")

	owner.add_pet(dog)
	owner.add_pet(cat)

	# Intentionally add tasks out of order by duration.
	dog.add_task(Task(description="Morning walk", time_minutes=25, frequency="daily"))
	cat.add_task(Task(description="Quick brush", time_minutes=5, frequency="daily"))
	dog.add_task(Task(description="Feed breakfast", time_minutes=10, frequency="daily"))
	cat.add_task(Task(description="Play session", time_minutes=20, frequency="weekly"))
	cat.add_task(Task(description="Clean litter box", time_minutes=15, frequency="daily"))

	# Mark one task complete to demonstrate status filtering.
	cat.tasks[0].mark_complete()

	scheduler = Scheduler()
	print_sorting_and_filtering_demo(owner, scheduler)
	print_todays_schedule(owner, scheduler)

	# DEMO: Show lightweight conflict detection with tasks at same time
	print("\n" + "=" * 70)
	print("Now demonstrating: CONFLICTING SCHEDULES WITH SAME-TIME TASKS")
	print("=" * 70)
	
	# Create a scenario with tasks scheduled at the same time
	conflict_owner = Owner(name="Alex", time_available_minutes=120, preferences=["morning"])
	mochi = Pet(name="Mochi", species="dog")
	luna = Pet(name="Luna", species="cat")
	
	conflict_owner.add_pet(mochi)
	conflict_owner.add_pet(luna)
	
	# Add tasks with SAME preferred start times - these will conflict!
	mochi.add_task(Task(
		description="Morning feeding",
		time_minutes=15,
		frequency="daily",
		preferred_start_minute=30  # Starts at 30 min, ends at 45 min
	))
	mochi.add_task(Task(
		description="Playtime",
		time_minutes=20,
		frequency="daily",
		preferred_start_minute=35  # Starts at 35 min, ends at 55 min - OVERLAPS!
	))
	
	luna.add_task(Task(
		description="Feeding",
		time_minutes=10,
		frequency="daily",
		preferred_start_minute=40  # Starts at 40 min, ends at 50 min - crosses multiple pets!
	))
	luna.add_task(Task(
		description="Grooming",
		time_minutes=20,
		frequency="daily",
		preferred_start_minute=85  # No conflict
	))
	
	conflict_scheduler = Scheduler()
	print_lightweight_conflict_detection_demo(conflict_owner, conflict_scheduler)


if __name__ == "__main__":
	main()
