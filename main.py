import sys

# Ensure emoji and Unicode characters render correctly on Windows terminals.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from pawpal_system import Owner, Pet, PriorityLevel, Scheduler, Task
from format_utils import (
    bold,
    cyan,
    dim,
    green,
    print_conflict_warnings,
    print_conflicts,
    print_owner_summary,
    print_schedule_table,
    print_section_header,
    print_task_table,
    yellow,
)


def demo_sorting_and_filtering(owner: Owner, scheduler: Scheduler) -> None:
    all_tasks = owner.get_all_tasks()

    print_task_table(all_tasks, title="All Tasks — Insertion Order")

    print_task_table(
        scheduler.sort_by_time(all_tasks, ascending=True),
        title="Sorted by Time — Shortest First",
    )

    print_task_table(
        scheduler.filter_tasks(owner, pet_name="Mochi"),
        title="Filtered — Pet: Mochi",
    )

    print_task_table(
        scheduler.filter_tasks(owner, completed=False),
        title="Filtered — Pending Tasks Only",
    )


def demo_schedule(owner: Owner, scheduler: Scheduler) -> None:
    plan = scheduler.build_daily_schedule(owner)
    warnings = scheduler.detect_conflicts_lightweight(owner)

    print_schedule_table(
        scheduled=plan["scheduled"],
        deferred=plan["deferred"],
        budget=owner.time_available_minutes,
        title=f"Daily Schedule  ·  {owner.name}  ·  {owner.time_available_minutes} min budget",
    )
    print_conflicts(plan["conflicts"])
    print_conflict_warnings(warnings)


def demo_conflict_detection(scheduler: Scheduler) -> None:
    print_section_header("Conflict Detection Demo — Overlapping Preferred Times")

    conflict_owner = Owner(name="Alex", time_available_minutes=120)
    mochi = Pet(name="Mochi", species="dog")
    luna = Pet(name="Luna", species="cat")
    conflict_owner.add_pet(mochi)
    conflict_owner.add_pet(luna)

    mochi.add_task(Task(
        description="Morning feeding",
        time_minutes=15,
        frequency="daily",
        preferred_start_minute=30,
    ))
    mochi.add_task(Task(
        description="Playtime",
        time_minutes=20,
        frequency="daily",
        preferred_start_minute=35,   # overlaps with Morning feeding (30–45)
    ))
    luna.add_task(Task(
        description="Feeding",
        time_minutes=10,
        frequency="daily",
        preferred_start_minute=40,   # overlaps across pets
    ))
    luna.add_task(Task(
        description="Grooming",
        time_minutes=20,
        frequency="daily",
        preferred_start_minute=85,   # no conflict
    ))

    print_owner_summary(conflict_owner)
    print_task_table(conflict_owner.get_all_tasks(), title="Tasks with Preferred Start Times")

    warnings = scheduler.detect_conflicts_lightweight(conflict_owner)
    print_conflict_warnings(warnings)


def demo_priority_scheduling() -> None:
    print_section_header("Priority-Based Scheduling Demo")

    owner = Owner(name="Jordan", time_available_minutes=60)
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)

    pet.add_task(Task("Administer eye drops", 5,  "daily",   PriorityLevel.HIGH))
    pet.add_task(Task("Morning walk",        30,  "daily",   PriorityLevel.LOW))
    pet.add_task(Task("Refill water bowl",    5,  "daily",   PriorityLevel.MEDIUM))
    pet.add_task(Task("Weekly grooming",     20,  "weekly",  PriorityLevel.MEDIUM))
    pet.add_task(Task("Vet appointment",     45,  "monthly", PriorityLevel.HIGH))

    scheduler = Scheduler()

    print_task_table(pet.tasks, title="Tasks — Insertion Order")

    print_task_table(
        scheduler.sort_by_time(pet.tasks),
        title="sort_by_time  (duration only — priority ignored)",
    )

    print_task_table(
        scheduler.organize_tasks(owner),
        title="organize_tasks  (priority → frequency → duration)",
    )

    plan = scheduler.build_daily_schedule(owner)
    print_schedule_table(
        scheduled=plan["scheduled"],
        deferred=plan["deferred"],
        budget=owner.time_available_minutes,
        title="build_daily_schedule  (60 min budget, priority-ordered fill)",
    )


def demo_urgency_schedule() -> None:
    print_section_header("Urgency-Weighted Schedule Demo")

    from datetime import date, timedelta

    owner = Owner(name="Sam", time_available_minutes=90)
    pet = Pet(name="Luna", species="cat")
    owner.add_pet(pet)

    today = date.today()
    pet.add_task(Task(
        "Overdue vet checkup", 45, "monthly",
        priority=PriorityLevel.HIGH,
        due_date=today - timedelta(days=5),
    ))
    pet.add_task(Task(
        "Daily meds", 5, "daily",
        priority=PriorityLevel.HIGH,
    ))
    pet.add_task(Task(
        "Fur brushing", 15, "weekly",
        priority=PriorityLevel.MEDIUM,
    ))
    pet.add_task(Task(
        "Play session", 20, "as-needed",
        priority=PriorityLevel.LOW,
    ))

    scheduler = Scheduler()
    plan = scheduler.build_urgency_prioritized_schedule(owner, current_date=today)
    print_schedule_table(
        scheduled=plan["scheduled"],
        deferred=plan["deferred"],
        budget=owner.time_available_minutes,
        title="Urgency-Prioritized Schedule  (overdue items first)",
        urgency_scores=plan["urgency_scores"],
    )


def main() -> None:
    owner = Owner(name="Jordan", time_available_minutes=60, preferences=["morning"])
    dog = Pet(name="Mochi", species="dog")
    cat = Pet(name="Luna", species="cat")
    owner.add_pet(dog)
    owner.add_pet(cat)

    dog.add_task(Task("Morning walk",    25, "daily"))
    cat.add_task(Task("Quick brush",      5, "daily"))
    dog.add_task(Task("Feed breakfast",  10, "daily"))
    cat.add_task(Task("Play session",    20, "weekly"))
    cat.add_task(Task("Clean litter box", 15, "daily"))

    cat.tasks[0].mark_complete()   # mark "Quick brush" done

    scheduler = Scheduler()

    print_owner_summary(owner)
    demo_sorting_and_filtering(owner, scheduler)
    demo_schedule(owner, scheduler)
    demo_conflict_detection(scheduler)
    demo_priority_scheduling()
    demo_urgency_schedule()


if __name__ == "__main__":
    main()
