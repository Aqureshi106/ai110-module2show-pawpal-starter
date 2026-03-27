classDiagram
class Owner {
        +name: str
    + timeAvailableMinutes: int
        + preferences: list
    }

class Pet {
        +name: str
    + species: str
    }

class Task {
        +title: str
    + durationMinutes: int
        + priority: str
    }

class TaskManager {
        +tasks: Task[]
    + addTask(title, duration, priority) void
        +editTask(taskId, updates) void
            +listTasks() Task[]
    }

class DailyScheduleGenerator {
        +schedule: Task[]
    + generateSchedule(timeAvailable, preferences) Task[]
        + explainPlan() str
    }

    Owner "1" -- > "1..*" Pet: has
    TaskManager "1" -- > "*" Task: manages
DailyScheduleGenerator..> Owner : uses constraints
DailyScheduleGenerator..> Pet : plans for
    DailyScheduleGenerator..> TaskManager : uses tasks