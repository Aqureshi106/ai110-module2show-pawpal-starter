classDiagram
class PriorityLevel {
    << enumeration >>
    LOW
MEDIUM
HIGH
}

class Owner {
    +name: str
    + time_available_minutes: int
        + preferences: List[str]
            + pets: List[Pet]
                + add_pet(pet)
                + get_all_tasks() List[Task]
}

class Pet {
    +name: str
    + species: str
        + tasks: List[Task]
            + add_task(task)
            + list_tasks() List[Task]
}

class Task {
    +description: str
    + time_minutes: int
        + frequency: str
            + completed: bool
                + id: str
                    + pet_name: Optional[str]
                        + last_completed_day: Optional[int]
                            + preferred_start_minute: Optional[int]
                                + due_date: Optional[date]
                                    + title: str
                                        + duration_minutes: int
                                            + mark_completed(current_day, completed_on)
                                            + mark_complete(current_day, completed_on)
}

class ScheduledTask {
    +task_id: str
    + task_title: str
        + start_minute: int
            + end_minute: int
                + reason: str
}

class DailyPlan {
    +scheduled: List[ScheduledTask]
    + deferred_task_ids: List[str]
        + summary_reasoning: str
}

class ConflictWarning {
    +level: str
    + message: str
        + affected_tasks: List[str]
            + pet_names: List[str]
                + __str__() str
}

class LightweightConflictDetector {
    +safe_has_time_overlap(start1, end1, start2, end2) bool
    + validate_task_duration(task) Optional[ConflictWarning]
        + check_time_budget(tasks, available_minutes) Optional[ConflictWarning]
            + check_preferred_time_overlaps(tasks) List[ConflictWarning]
                + check_scheduled_overlaps(scheduled_tasks) List[ConflictWarning]
                    + check_duplicate_recurring_tasks(tasks) List[ConflictWarning]
                        + detect_all_conflicts(tasks, scheduled_tasks, available_minutes) List[ConflictWarning]
}

class TaskManager {
    +tasks: List[Task]
    + add_task(description, time_minutes, frequency, pet_name) Task
        + edit_task(task_id, updates)
        + list_tasks() List[Task]
}

class Scheduler {
    +frequency_order: Dict[str, int]
    + retrieve_all_tasks(owner) List[Task]
        + sort_by_time(tasks, ascending) List[Task]
            + sort_tasks_by_time(tasks, ascending) List[Task]
                + filter_tasks(owner, pet_name, completed) List[Task]
                    + is_task_due(task, day_index, current_date) bool
                        + organize_tasks(owner, day_index, pet_name, include_completed) List[Task]
                            + detect_conflicts(tasks, available_minutes) List[str]
                                + detect_scheduled_time_conflicts(scheduled_tasks) List[str]
                                    + detect_conflicts_lightweight(owner, scheduled_tasks) List[ConflictWarning]
                                        + build_daily_schedule(owner, day_index, pet_name) Dict[str, Any]
                                            + tasks_by_pet(owner) Dict[str, List[Task]]
                                                + mark_task_complete(owner, task_id, current_day, current_date) Optional[Task]
}

class DailyScheduleGenerator {
    +plan: DailyPlan
    + scheduler: Scheduler
        + generate_schedule(owner, pet, tasks) DailyPlan
            + explain_plan(plan) str
}

Owner "1" o-- "*" Pet: owns
Pet "1" o-- "*" Task: has
TaskManager "1" o-- "*" Task: manages
DailyPlan "1" o-- "*" ScheduledTask: contains

Scheduler..> Owner : retrieves from
Scheduler..> Task : organizes
Scheduler..> ScheduledTask : builds windows
Scheduler..> LightweightConflictDetector : delegates
Scheduler..> ConflictWarning : returns

LightweightConflictDetector..> Task
LightweightConflictDetector..> ScheduledTask
LightweightConflictDetector..> ConflictWarning

DailyScheduleGenerator * --DailyPlan
DailyScheduleGenerator * --Scheduler
DailyScheduleGenerator..> Owner
DailyScheduleGenerator..> Pet
DailyScheduleGenerator..> Task