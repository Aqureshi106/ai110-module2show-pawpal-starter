from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Owner:
	name: str
	time_available_minutes: int
	preferences: List[str] = field(default_factory=list)


@dataclass
class Pet:
	name: str
	species: str


@dataclass
class Task:
	title: str
	duration_minutes: int
	priority: str


class TaskManager:
	def __init__(self) -> None:
		self.tasks: List[Task] = []

	def add_task(self, title: str, duration: int, priority: str) -> None:
		pass

	def edit_task(self, task_id: int, updates: Dict[str, Any]) -> None:
		pass

	def list_tasks(self) -> List[Task]:
		pass


class DailyScheduleGenerator:
	def __init__(self) -> None:
		self.schedule: List[Task] = []

	def generate_schedule(
		self,
		time_available: int,
		preferences: List[str],
		owner: Owner,
		pet: Pet,
		task_manager: TaskManager,
	) -> List[Task]:
		pass

	def explain_plan(self) -> str:
		pass
