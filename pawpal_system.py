from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class PriorityLevel(str, Enum):
	LOW = "low"
	MEDIUM = "medium"
	HIGH = "high"


@dataclass
class Owner:
	name: str
	time_available_minutes: int
	preferences: List[str] = field(default_factory=list)
	pets: List[Pet] = field(default_factory=list)

	def add_pet(self, pet: Pet) -> None:
		"""Add a pet to this owner's managed pet list."""
		self.pets.append(pet)

	def get_all_tasks(self) -> List[Task]:
		"""Return a combined list of tasks across all owned pets."""
		all_tasks: List[Task] = []
		for pet in self.pets:
			all_tasks.extend(pet.tasks)
		return all_tasks


@dataclass
class Pet:
	name: str
	species: str
	tasks: List[Task] = field(default_factory=list)

	def add_task(self, task: Task) -> None:
		"""Attach a task to this pet and default the task pet name if missing."""
		if task.pet_name is None:
			task.pet_name = self.name
		self.tasks.append(task)

	def list_tasks(self) -> List[Task]:
		"""Return a shallow copy of this pet's tasks."""
		return list(self.tasks)


@dataclass
class Task:
	description: str
	time_minutes: int
	frequency: str
	completed: bool = False
	id: str = field(default_factory=lambda: str(uuid4())[:8])
	pet_name: Optional[str] = None
	last_completed_day: Optional[int] = None
	preferred_start_minute: Optional[int] = None
	due_date: Optional[date] = None

	@property
	def title(self) -> str:
		"""Expose description as a title-compatible alias."""
		return self.description

	@property
	def duration_minutes(self) -> int:
		"""Expose time_minutes as a duration-compatible alias."""
		return self.time_minutes

	def mark_completed(self, current_day: Optional[int] = None, completed_on: Optional[date] = None) -> None:
		"""Mark this task as completed."""
		self.completed = True
		if current_day is not None:
			self.last_completed_day = current_day
		if completed_on is not None:
			self.due_date = completed_on

	def mark_complete(self, current_day: Optional[int] = None, completed_on: Optional[date] = None) -> None:
		"""Mark this task as completed using the legacy method name."""
		self.mark_completed(current_day=current_day, completed_on=completed_on)


@dataclass
class ScheduledTask:
	task_id: str
	task_title: str
	start_minute: int
	end_minute: int
	reason: str


@dataclass
class DailyPlan:
	scheduled: List[ScheduledTask] = field(default_factory=list)
	deferred_task_ids: List[str] = field(default_factory=list)
	summary_reasoning: str = ""


@dataclass
class ConflictWarning:
	"""Lightweight warning representation for scheduling conflicts."""
	level: str  # "info", "warning", "critical"
	message: str
	affected_tasks: List[str] = field(default_factory=list)
	pet_names: List[str] = field(default_factory=list)

	def __str__(self) -> str:
		"""Return a readable warning message."""
		level_indicator = {
			"info": "ℹ️",
			"warning": "⚠️",
			"critical": "❌",
		}.get(self.level, "•")
		return f"{level_indicator} [{self.level.upper()}] {self.message}"


class LightweightConflictDetector:
	"""Safe, non-crashing conflict detection strategy that returns warnings."""

	@staticmethod
	def safe_has_time_overlap(
		start1: Optional[int], end1: Optional[int],
		start2: Optional[int], end2: Optional[int]
	) -> bool:
		"""Safely check for time overlap, handling None values gracefully."""
		try:
			if any(v is None for v in [start1, end1, start2, end2]):
				return False
			if any(v < 0 for v in [start1, end1, start2, end2]):
				return False
			if start1 >= end1 or start2 >= end2:
				return False
			return start1 < end2 and start2 < end1
		except (TypeError, ValueError):
			return False

	@staticmethod
	def validate_task_duration(task: Task) -> Optional[ConflictWarning]:
		"""Check task duration and return warning if invalid."""
		try:
			if task.time_minutes is None:
				return ConflictWarning(
					level="warning",
					message=f"Task '{task.description}' has no duration set.",
					affected_tasks=[task.id],
					pet_names=[task.pet_name or "Unknown"],
				)
			if task.time_minutes <= 0:
				return ConflictWarning(
					level="warning",
					message=f"Task '{task.description}' has invalid duration ({task.time_minutes} min).",
					affected_tasks=[task.id],
					pet_names=[task.pet_name or "Unknown"],
				)
		except Exception:
			pass
		return None

	@staticmethod
	def check_time_budget(tasks: List[Task], available_minutes: int) -> Optional[ConflictWarning]:
		"""Check if total task time exceeds availability."""
		try:
			if available_minutes <= 0:
				return ConflictWarning(
					level="info",
					message=f"Available time is not positive ({available_minutes} min).",
				)
			total_minutes = sum(
				task.time_minutes for task in tasks
				if task.time_minutes and task.time_minutes > 0 and not task.completed
			)
			if total_minutes > available_minutes:
				return ConflictWarning(
					level="warning",
					message=f"Total task time ({total_minutes} min) exceeds available time ({available_minutes} min). {total_minutes - available_minutes} min over budget.",
					affected_tasks=[t.id for t in tasks if t.time_minutes and t.time_minutes > 0],
				)
		except Exception:
			pass
		return None

	@staticmethod
	def check_preferred_time_overlaps(tasks: List[Task]) -> List[ConflictWarning]:
		"""Check for overlapping preferred start times."""
		warnings: List[ConflictWarning] = []
		try:
			preferred_windows = [
				(task.pet_name or "Unknown", task.description, 
				 task.preferred_start_minute, 
				 (task.preferred_start_minute or 0) + (task.time_minutes or 0), 
				 task.id)
				for task in tasks
				if task.preferred_start_minute is not None and (task.time_minutes or 0) > 0
			]

			for idx in range(len(preferred_windows)):
				for jdx in range(idx + 1, len(preferred_windows)):
					pet1, desc1, start1, end1, id1 = preferred_windows[idx]
					pet2, desc2, start2, end2, id2 = preferred_windows[jdx]

					if LightweightConflictDetector.safe_has_time_overlap(start1, end1, start2, end2):
						if pet1 == pet2:
							message = f"Pet '{pet1}' has overlapping tasks: '{desc1}' and '{desc2}'."
						else:
							message = f"Different pets overlap: '{desc1}' ({pet1}) at {start1}-{end1} min overlaps with '{desc2}' ({pet2}) at {start2}-{end2} min."
						
						warnings.append(ConflictWarning(
							level="warning",
							message=message,
							affected_tasks=[id1, id2],
							pet_names=[pet1, pet2],
						))
		except Exception:
			pass
		return warnings

	@staticmethod
	def check_scheduled_overlaps(scheduled_tasks: List[ScheduledTask]) -> List[ConflictWarning]:
		"""Check for overlapping scheduled task times."""
		warnings: List[ConflictWarning] = []
		try:
			for idx in range(len(scheduled_tasks)):
				for jdx in range(idx + 1, len(scheduled_tasks)):
					task1 = scheduled_tasks[idx]
					task2 = scheduled_tasks[jdx]

					if LightweightConflictDetector.safe_has_time_overlap(
						task1.start_minute, task1.end_minute,
						task2.start_minute, task2.end_minute
					):
						warnings.append(ConflictWarning(
							level="warning",
							message=f"Scheduled task overlap: '{task1.task_title}' ({task1.start_minute}-{task1.end_minute} min) "
									 f"overlaps with '{task2.task_title}' ({task2.start_minute}-{task2.end_minute} min).",
							affected_tasks=[task1.task_id, task2.task_id],
						))
		except Exception:
			pass
		return warnings

	@staticmethod
	def check_duplicate_recurring_tasks(tasks: List[Task]) -> List[ConflictWarning]:
		"""Check for duplicate recurring tasks."""
		warnings: List[ConflictWarning] = []
		try:
			seen: Dict[tuple[str, str, str], List[str]] = {}
			for task in tasks:
				key = (
					task.pet_name or "",
					task.description.strip().lower() if task.description else "",
					task.frequency.strip().lower() if task.frequency else "",
				)
				if key not in seen:
					seen[key] = []
				seen[key].append(task.id)

			for (pet_name, description, frequency), task_ids in seen.items():
				if len(task_ids) > 1:
					warnings.append(ConflictWarning(
						level="info",
						message=f"Duplicate task for '{pet_name}': '{description}' ({frequency}) appears {len(task_ids)} times. "
								 f"This may be intentional if recurring tasks were created.",
						affected_tasks=task_ids,
						pet_names=[pet_name] if pet_name else [],
					))
		except Exception:
			pass
		return warnings

	@staticmethod
	def detect_all_conflicts(
		tasks: List[Task],
		scheduled_tasks: Optional[List[ScheduledTask]] = None,
		available_minutes: int = 60
	) -> List[ConflictWarning]:
		"""Comprehensive, lightweight conflict detection that never crashes."""
		all_warnings: List[ConflictWarning] = []

		# Check task durations
		for task in tasks:
			duration_warning = LightweightConflictDetector.validate_task_duration(task)
			if duration_warning:
				all_warnings.append(duration_warning)

		# Check time budget
		time_budget_warning = LightweightConflictDetector.check_time_budget(tasks, available_minutes)
		if time_budget_warning:
			all_warnings.append(time_budget_warning)

		# Check preferred time overlaps
		all_warnings.extend(LightweightConflictDetector.check_preferred_time_overlaps(tasks))

		# Check scheduled overlaps if provided
		if scheduled_tasks:
			all_warnings.extend(LightweightConflictDetector.check_scheduled_overlaps(scheduled_tasks))

		# Check for duplicate recurring tasks
		all_warnings.extend(LightweightConflictDetector.check_duplicate_recurring_tasks(tasks))

		return all_warnings


class TaskManager:
	def __init__(self) -> None:
		"""Initialize an in-memory task store."""
		self.tasks: List[Task] = []

	def add_task(
		self,
		description: str,
		time_minutes: int,
		frequency: str,
		pet_name: Optional[str] = None,
	) -> Task:
		"""Create and store a task, then return the new task object."""
		task = Task(
			description=description,
			time_minutes=time_minutes,
			frequency=frequency,
			pet_name=pet_name,
		)
		self.tasks.append(task)
		return task

	def edit_task(self, task_id: str, updates: Dict[str, Any]) -> None:
		"""Update mutable fields on a task identified by task_id."""
		for task in self.tasks:
			if task.id == task_id:
				for key, value in updates.items():
					if hasattr(task, key):
						setattr(task, key, value)
				return
		raise ValueError(f"Task with id '{task_id}' not found")

	def list_tasks(self) -> List[Task]:
		"""Return a shallow copy of all tracked tasks."""
		return list(self.tasks)


class Scheduler:
	"""Brain of the system: retrieves, organizes, and manages tasks across pets."""

	frequency_order: Dict[str, int] = {
		"daily": 0,
		"weekly": 1,
		"monthly": 2,
		"as-needed": 3,
	}

	@staticmethod
	def _has_time_overlap(start1: int, end1: int, start2: int, end2: int) -> bool:
		"""Return whether two half-open minute windows overlap.

		Args:
			start1: Start minute of the first window.
			end1: End minute of the first window.
			start2: Start minute of the second window.
			end2: End minute of the second window.

		Returns:
			True when the intervals intersect (not just touch), otherwise False.
		"""
		return start1 < end2 and start2 < end1

	def detect_scheduled_time_conflicts(self, scheduled_tasks: List[ScheduledTask]) -> List[str]:
		"""Detect pairwise overlaps in already-timed scheduled tasks.

		This method compares each task window against every later task window and
		reports a conflict message whenever time ranges overlap.

		Args:
			scheduled_tasks: Scheduled task entries with concrete start/end minutes.

		Returns:
			A list of human-readable conflict messages. Empty when no overlaps exist.
		"""
		conflicts: List[str] = []
		
		# Check for overlaps between any two scheduled tasks
		for idx in range(len(scheduled_tasks)):
			for jdx in range(idx + 1, len(scheduled_tasks)):
				task1 = scheduled_tasks[idx]
				task2 = scheduled_tasks[jdx]
				
				# Check if time windows overlap
				if self._has_time_overlap(task1.start_minute, task1.end_minute, 
										   task2.start_minute, task2.end_minute):
					conflicts.append(
						f"Time conflict detected: '{task1.task_title}' ({task1.start_minute}-{task1.end_minute} min) "
						f"overlaps with '{task2.task_title}' ({task2.start_minute}-{task2.end_minute} min)."
					)
		
		return conflicts

	def detect_conflicts_lightweight(
		self,
		owner: Owner,
		scheduled_tasks: Optional[List[ScheduledTask]] = None,
	) -> List[ConflictWarning]:
		"""
		Lightweight conflict detection that never crashes - returns warning messages.
		
		This method is resilient and will not raise exceptions even with malformed data.
		All conflicts are returned as structured warnings that can be logged or displayed.
		"""
		try:
			tasks = self.retrieve_all_tasks(owner)
			return LightweightConflictDetector.detect_all_conflicts(
				tasks=tasks,
				scheduled_tasks=scheduled_tasks,
				available_minutes=owner.time_available_minutes,
			)
		except Exception as e:
			# Last-resort safety: if anything goes wrong, return a single warning
			return [
				ConflictWarning(
					level="info",
					message=f"Conflict detection encountered an issue (this is safe and non-fatal): {str(e)[:50]}",
				)
			]

	def retrieve_all_tasks(self, owner: Owner) -> List[Task]:
		"""Get every task belonging to the owner's pets."""
		return owner.get_all_tasks()

	def sort_by_time(self, tasks: List[Task], ascending: bool = True) -> List[Task]:
		"""Sort a task list by duration in minutes."""
		return sorted(tasks, key=lambda task: task.time_minutes, reverse=not ascending)

	def sort_tasks_by_time(self, tasks: List[Task], ascending: bool = True) -> List[Task]:
		"""Compatibility alias for sort_by_time."""
		return self.sort_by_time(tasks, ascending=ascending)

	def filter_tasks(
		self,
		owner: Owner,
		pet_name: Optional[str] = None,
		completed: Optional[bool] = None,
	) -> List[Task]:
		"""Filter tasks by pet and completion status."""
		tasks = self.retrieve_all_tasks(owner)
		if pet_name is not None:
			tasks = [task for task in tasks if task.pet_name == pet_name]
		if completed is not None:
			tasks = [task for task in tasks if task.completed is completed]
		return tasks

	def is_task_due(self, task: Task, day_index: int = 0, current_date: Optional[date] = None) -> bool:
		"""Determine whether a recurring task is due on a given day index."""
		if task.due_date is not None:
			reference_date = current_date or date.today()
			return reference_date >= task.due_date

		frequency = task.frequency.lower()
		if frequency == "as-needed":
			return not task.completed

		interval_days = {
			"daily": 1,
			"weekly": 7,
			"monthly": 30,
		}.get(frequency)

		if interval_days is None:
			return not task.completed

		if task.last_completed_day is None:
			return True

		return (day_index - task.last_completed_day) >= interval_days

	def organize_tasks(
		self,
		owner: Owner,
		day_index: int = 0,
		pet_name: Optional[str] = None,
		include_completed: bool = False,
	) -> List[Task]:
		"""Build the ordered candidate task list for planning.

		Algorithm:
			1. Filter tasks by owner/pet.
			2. Keep only tasks that are due for the provided day.
			3. Optionally drop completed tasks.
			4. Sort by completion state, frequency rank, and duration.

		Args:
			owner: Owner whose pet tasks should be considered.
			day_index: Day index used for recurrence checks.
			pet_name: Optional pet filter.
			include_completed: Whether completed tasks should remain in output.

		Returns:
			A deterministically ordered list used by downstream schedulers.
		"""
		tasks = self.filter_tasks(owner, pet_name=pet_name)
		tasks = [task for task in tasks if self.is_task_due(task, day_index=day_index)]

		if not include_completed:
			tasks = [task for task in tasks if not task.completed]

		return sorted(
			tasks,
			key=lambda task: (
				task.completed,
				self.frequency_order.get(task.frequency.lower(), 99),
				task.time_minutes,
			),
		)

	def detect_conflicts(self, tasks: List[Task], available_minutes: int) -> List[str]:
		"""Run pre-schedule conflict checks across a task set.

		Checks include:
			- Total pending minutes exceeding available time.
			- Non-positive task durations.
			- Duplicate recurring task signatures.
			- Preferred-time overlaps (same pet and cross-pet).

		Args:
			tasks: Task list to validate.
			available_minutes: Daily time budget used for over-budget detection.

		Returns:
			A list of conflict messages. Empty when no conflicts are found.
		"""
		conflicts: List[str] = []

		total_minutes = sum(task.time_minutes for task in tasks if not task.completed)
		if total_minutes > available_minutes:
			conflicts.append(
				f"Total pending task time ({total_minutes} min) exceeds available time ({available_minutes} min)."
			)

		seen: Dict[tuple[str, str, str], int] = {}
		for task in tasks:
			if task.time_minutes <= 0:
				conflicts.append(f"Task '{task.description}' has non-positive duration.")

			key = (
				task.pet_name or "",
				task.description.strip().lower(),
				task.frequency.strip().lower(),
			)
			seen[key] = seen.get(key, 0) + 1

		for (pet_name, description, frequency), count in seen.items():
			if count > 1:
				conflicts.append(
					f"Duplicate recurring task detected for pet '{pet_name}': '{description}' ({frequency}) x{count}."
				)

		# Build preferred-time windows for all tasks with preferred start times
		preferred_windows = [
			(task.pet_name or "", task.description, task.preferred_start_minute, task.preferred_start_minute + task.time_minutes, task.id)
			for task in tasks
			if task.preferred_start_minute is not None and task.time_minutes > 0
		]
		
		# Detect overlaps within same pet and across different pets
		for idx in range(len(preferred_windows)):
			for jdx in range(idx + 1, len(preferred_windows)):
				prev = preferred_windows[idx]
				curr = preferred_windows[jdx]
				
				# Check for time overlap
				if self._has_time_overlap(prev[2], prev[3], curr[2], curr[3]):
					if prev[0] == curr[0]:
						# Same pet conflict
						conflicts.append(
							f"Preferred-time overlap for pet '{curr[0]}': '{prev[1]}' and '{curr[1]}'."
						)
					else:
						# Different pets scheduled at same time
						conflicts.append(
							f"Time conflict across different pets: '{prev[1]}' for {prev[0]} "
							f"({prev[2]}-{prev[3]} min) overlaps with '{curr[1]}' for {curr[0]} "
							f"({curr[2]}-{curr[3]} min)."
						)

		return conflicts

	def build_daily_schedule(
		self,
		owner: Owner,
		day_index: int = 0,
		pet_name: Optional[str] = None,
	) -> Dict[str, Any]:
		"""Generate a greedy daily plan constrained by owner available time.

		Algorithm:
			1. Build an ordered task list via ``organize_tasks``.
			2. Schedule tasks sequentially until the time budget is reached.
			3. Defer tasks that no longer fit.
			4. Convert accepted tasks to ``ScheduledTask`` windows.
			5. Aggregate preferred-time and scheduled-time conflict messages.

		Args:
			owner: Owner providing the task pool and time budget.
			day_index: Day index used for due-date/recurrence filtering.
			pet_name: Optional single-pet scope.

		Returns:
			Dictionary with ``scheduled``, ``deferred``, and ``conflicts`` keys.
		"""
		organized = self.organize_tasks(owner, day_index=day_index, pet_name=pet_name)
		scheduled: List[Task] = []
		deferred: List[Task] = []
		current_minute = 0

		for task in organized:
			if current_minute + task.time_minutes <= owner.time_available_minutes:
				scheduled.append(task)
				current_minute += task.time_minutes
			else:
				deferred.append(task)

		# Convert scheduled tasks to ScheduledTask format to detect time conflicts
		scheduled_tasks: List[ScheduledTask] = []
		current_time = 0
		for task in scheduled:
			scheduled_tasks.append(
				ScheduledTask(
					task_id=task.id,
					task_title=task.description,
					start_minute=current_time,
					end_minute=current_time + task.time_minutes,
					reason=f"Scheduled based on frequency '{task.frequency}'.",
				)
			)
			current_time += task.time_minutes

		# Detect both types of conflicts
		all_conflicts = self.detect_conflicts(organized, owner.time_available_minutes)
		scheduled_conflicts = self.detect_scheduled_time_conflicts(scheduled_tasks)
		all_conflicts.extend(scheduled_conflicts)

		return {
			"scheduled": scheduled,
			"deferred": deferred,
			"conflicts": all_conflicts,
		}

	def tasks_by_pet(self, owner: Owner) -> Dict[str, List[Task]]:
		"""Return tasks grouped by pet name for the given owner."""
		return {pet.name: pet.list_tasks() for pet in owner.pets}

	def _find_task_pet(self, owner: Owner, task: Task) -> Optional[Pet]:
		"""Find the pet that owns the task object."""
		for pet in owner.pets:
			if task in pet.tasks:
				return pet
		return None

	def _create_next_occurrence(self, task: Task, current_day: int, current_date: date) -> Optional[Task]:
		"""Create a follow-up task for recurring daily/weekly tasks."""
		frequency = task.frequency.lower()
		if frequency not in {"daily", "weekly"}:
			return None

		offset_days = 1 if frequency == "daily" else 7
		next_due_date = current_date + timedelta(days=offset_days)

		return Task(
			description=task.description,
			time_minutes=task.time_minutes,
			frequency=task.frequency,
			pet_name=task.pet_name,
			last_completed_day=current_day,
			preferred_start_minute=task.preferred_start_minute,
			due_date=next_due_date,
		)

	def mark_task_complete(
		self,
		owner: Owner,
		task_id: str,
		current_day: int = 0,
		current_date: Optional[date] = None,
	) -> Optional[Task]:
		"""Mark a task complete and optionally spawn its next recurring occurrence."""
		completion_date = current_date or date.today()
		for task in owner.get_all_tasks():
			if task.id == task_id:
				if task.completed:
					return None

				task.mark_completed(current_day=current_day, completed_on=completion_date)
				next_task = self._create_next_occurrence(
					task,
					current_day=current_day,
					current_date=completion_date,
				)

				if next_task is not None:
					pet = self._find_task_pet(owner, task)
					if pet is not None:
						pet.add_task(next_task)
						return next_task

				return None
		raise ValueError(f"Task with id '{task_id}' not found")


class DailyScheduleGenerator:
	def __init__(self) -> None:
		"""Initialize an empty daily plan and shared scheduler helper."""
		self.plan: DailyPlan = DailyPlan()
		self.scheduler = Scheduler()

	def generate_schedule(
		self,
		owner: Owner,
		pet: Pet,
		tasks: List[Task],
	) -> DailyPlan:
		"""Build a pet-specific plan that fits within the owner's time budget."""
		available_minutes = owner.time_available_minutes
		current_minute = 0

		# Keep this generator pet-focused while relying on Scheduler ordering behavior.
		pet_tasks = [
			task
			for task in sorted(
				tasks,
				key=lambda t: (
					t.completed,
					self.scheduler.frequency_order.get(t.frequency.lower(), 99),
					t.time_minutes,
				),
			)
			if task.pet_name in (None, pet.name)
		]

		scheduled: List[ScheduledTask] = []
		deferred: List[str] = []

		for task in pet_tasks:
			if task.completed:
				continue
			if current_minute + task.time_minutes <= available_minutes:
				scheduled.append(
					ScheduledTask(
						task_id=task.id,
						task_title=task.description,
						start_minute=current_minute,
						end_minute=current_minute + task.time_minutes,
						reason=f"Scheduled based on frequency '{task.frequency}' and available time.",
					)
				)
				current_minute += task.time_minutes
			else:
				deferred.append(task.id)

		self.plan = DailyPlan(
			scheduled=scheduled,
			deferred_task_ids=deferred,
			summary_reasoning=f"Scheduled {len(scheduled)} tasks for {pet.name}; deferred {len(deferred)} due to time limit.",
		)
		return self.plan

	def explain_plan(self, plan: DailyPlan) -> str:
		"""Return a readable text summary of a generated daily plan."""
		if not plan.scheduled:
			return "No tasks were scheduled today."

		lines = ["Daily schedule:"]
		for item in plan.scheduled:
			lines.append(
				f"- {item.task_title} ({item.start_minute}-{item.end_minute} min): {item.reason}"
			)

		if plan.deferred_task_ids:
			lines.append(f"Deferred tasks: {len(plan.deferred_task_ids)}")

		if plan.summary_reasoning:
			lines.append(plan.summary_reasoning)

		return "\n".join(lines)
