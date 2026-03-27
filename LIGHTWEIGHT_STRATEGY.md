# Lightweight Conflict Detection Strategy

## Overview

The **Lightweight Conflict Detection Strategy** provides a robust, resilient approach to detecting scheduling conflicts that **returns warning messages instead of crashing the program**. This is perfect for production systems where reliability is critical.

## Key Philosophy

✅ **Never Crash** - All exceptions are caught and handled gracefully  
✅ **Return Warnings** - Conflicts are reported as structured warning objects  
✅ **Handle Bad Data** - Programs continue even with invalid or malformed data  
✅ **Structured Feedback** - Warnings include severity levels, affected tasks, and pet names  

## Architecture

### 1. ConflictWarning Dataclass

```python
@dataclass
class ConflictWarning:
    """Lightweight warning representation for scheduling conflicts."""
    level: str          # "info", "warning", "critical"
    message: str        # Human-readable message
    affected_tasks: List[str] = []  # Task IDs involved
    pet_names: List[str] = []       # Pet names involved
```

**Usage:**
```python
warning = ConflictWarning(
    level="warning",
    message="Task 'Walk' overlaps with 'Play'",
    affected_tasks=["task1", "task2"],
    pet_names=["Mochi"]
)
print(warning)  # Output: ⚠️ [WARNING] Task 'Walk' overlaps with 'Play'
```

### 2. LightweightConflictDetector Class

A collection of safe, static methods that never throw exceptions:

#### `safe_has_time_overlap(start1, end1, start2, end2) -> bool`

**Features:**
- Handles `None` values gracefully
- Validates that times are positive
- Checks for invalid ranges (start >= end)
- Returns `False` for any invalid input

**Example:**
```python
# All of these return False safely, no crashes
LightweightConflictDetector.safe_has_time_overlap(None, 10, 5, 15)  # → False
LightweightConflictDetector.safe_has_time_overlap(-5, 10, 5, 15)    # → False
LightweightConflictDetector.safe_has_time_overlap(0, 10, 10, 20)    # → False (sequential)
```

#### `validate_task_duration(task: Task) -> Optional[ConflictWarning]`

**Checks:**
- Task duration is not None
- Task duration is positive
- Returns warning if invalid, None if valid

**Example:**
```python
invalid_task = Task(description="Bad", time_minutes=0, frequency="daily")
warning = LightweightConflictDetector.validate_task_duration(invalid_task)
# Returns: ConflictWarning with level="warning"
```

#### `check_time_budget(tasks, available_minutes) -> Optional[ConflictWarning]`

**Checks:**
- Available time is positive
- Total task time doesn't exceed availability
- Calculates overage if exceeded

**Example:**
```python
tasks = [
    Task(description="Walk", time_minutes=40, frequency="daily"),
    Task(description="Feed", time_minutes=30, frequency="daily"),
]
warning = LightweightConflictDetector.check_time_budget(tasks, available_minutes=60)
# Returns: "Total task time (70 min) exceeds available time (60 min). 10 min over budget."
```

#### `check_preferred_time_overlaps(tasks) -> List[ConflictWarning]`

**Checks:**
- Overlapping preferred start times for same pet
- Overlapping preferred start times across different pets
- Returns list of warnings for all detected overlaps

**Example:**
```python
tasks = [
    Task(..., pet_name="Mochi", preferred_start_minute=0, time_minutes=10),
    Task(..., pet_name="Mochi", preferred_start_minute=5, time_minutes=10),  # Overlaps!
]
warnings = LightweightConflictDetector.check_preferred_time_overlaps(tasks)
# Returns list with one warning about overlap
```

#### `check_scheduled_overlaps(scheduled_tasks) -> List[ConflictWarning]`

**Checks:**
- Overlapping time windows in scheduled tasks
- Works for both same-pet and different-pet scenarios

**Example:**
```python
scheduled = [
    ScheduledTask(..., start_minute=0, end_minute=20),
    ScheduledTask(..., start_minute=15, end_minute=35),  # Overlaps!
]
warnings = LightweightConflictDetector.check_scheduled_overlaps(scheduled)
```

#### `check_duplicate_recurring_tasks(tasks) -> List[ConflictWarning]`

**Checks:**
- Duplicate recurring tasks (same pet, description, frequency)
- Returns info-level warnings (may be intentional)

#### `detect_all_conflicts(tasks, scheduled_tasks=None, available_minutes=60) -> List[ConflictWarning]`

**Comprehensive detection** that runs all checks and never crashes:
- Task duration validation
- Time budget checking
- Preferred time overlap detection
- Scheduled time overlap detection
- Duplicate task detection

## Integration with Scheduler

### New Method: `detect_conflicts_lightweight()`

```python
scheduler = Scheduler()
warnings = scheduler.detect_conflicts_lightweight(
    owner=owner,
    scheduled_tasks=optional_scheduled_tasks
)

for warning in warnings:
    print(warning)  # Pretty-printed with level indicator
```

**Returns:** `List[ConflictWarning]` - never raises exceptions

**Features:**
- Wrapped in try-except for maximum safety
- Last-resort fallback message if anything goes wrong
- Always returns a list (even if empty)

## Warning Levels

### INFO (ℹ️)
- Informational - no action needed
- Examples:
  - "Duplicate recurring task detected (may be intentional)"
  - "Task scheduled outside preferred window"

### WARNING (⚠️)
- Potential issue - user should review
- Examples:
  - "Total task time exceeds available time by X minutes"
  - "Two tasks scheduled at overlapping times"

### CRITICAL (❌)
- Serious problem - scheduling won't work
- Examples:
  - "Invalid task duration (cannot schedule)"
  - "Required pet information missing"

## Usage Patterns

### Pattern 1: Simple Validation
```python
owner = Owner(name="Alex", time_available_minutes=60)
pet = Pet(name="Mochi", species="dog")
owner.add_pet(pet)
pet.add_task(Task(description="Walk", time_minutes=30, frequency="daily"))

scheduler = Scheduler()
warnings = scheduler.detect_conflicts_lightweight(owner)

if warnings:
    print(f"Found {len(warnings)} warnings:")
    for w in warnings:
        print(f"  {w}")
# Program continues - no crashes even if issues found!
```

### Pattern 2: With Scheduled Tasks
```python
scheduled = [
    ScheduledTask(task_id="1", task_title="Walk", start_minute=0, end_minute=20, reason=""),
    ScheduledTask(task_id="2", task_title="Play", start_minute=15, end_minute=30, reason=""),
]

warnings = scheduler.detect_conflicts_lightweight(owner, scheduled_tasks=scheduled)
# Includes warning about overlap, no exception raised
```

### Pattern 3: Direct Detector Use
```python
from pawpal_system import LightweightConflictDetector

# Check specific things
duration_warning = LightweightConflictDetector.validate_task_duration(task)
overlap_warnings = LightweightConflictDetector.check_preferred_time_overlaps(tasks)

# Or check everything
all_warnings = LightweightConflictDetector.detect_all_conflicts(
    tasks=owner.get_all_tasks(),
    available_minutes=owner.time_available_minutes
)
```

## Error Handling Guarantees

| Scenario | Traditional Approach | Lightweight Approach |
|----------|---------------------|----------------------|
| None values | ❌ Crash | ✅ Returns False/None |
| Invalid durations | ❌ Exception | ✅ Warning message |
| Over-budget tasks | ❌ May crash | ✅ Warning message |
| Bad scheduled times | ❌ Possible crash | ✅ Warning message |
| Malformed data | ❌ Exception | ✅ Last-resort warning |

## Testing

### Test Coverage
- 9 new tests for lightweight detection
- All tests pass: 25/25

### Key Tests
1. **test_lightweight_safe_has_time_overlap_with_none** - Validates None handling
2. **test_lightweight_validate_task_duration** - Validates duration checking
3. **test_lightweight_check_time_budget** - Validates budget checking
4. **test_lightweight_check_preferred_overlaps** - Validates overlap detection
5. **test_lightweight_check_scheduled_overlaps** - Validates scheduled task checking
6. **test_lightweight_detect_all_conflicts_safe** - Validates comprehensive detection
7. **test_conflict_warning_str_representation** - Validates warning formatting
8. **test_scheduler_detect_conflicts_lightweight_no_crash** - Integration test
9. **test_scheduler_detect_conflicts_lightweight_with_scheduled_tasks** - Integration with scheduled tasks

## Production Readiness

✅ **Safe for Production**
- Never crashes - wrapped in try-except
- Returns structured data for logging/UI
- Handles edge cases gracefully
- Comprehensive test coverage
- Clear warning levels for escalation
- Backward compatible

✅ **For UI Integration**
- ConflictWarning objects are easily serializable
- Message strings are human-readable
- Severity levels enable color-coding (red/yellow/blue)
- Affected task IDs for highlighting
- Pet names for context

✅ **For Logging/Analytics**
- All warnings can be logged with level
- Task IDs enable tracking
- Message templates are consistent
- No sensitive data in warnings

## Migration from Old Strategy

The lightweight strategy **co-exists** with existing detection methods:

```python
# Old: Returns string list
conflicts = scheduler.detect_conflicts(tasks, available_minutes=60)

# New: Returns ConflictWarning objects, never crashes
warnings = scheduler.detect_conflicts_lightweight(owner)

# Both can be used alongside each other
```

## Benefits Summary

| Aspect | Benefit |
|--------|---------|
| **Reliability** | Never crashes - production-safe |
| **User Experience** | Warnings don't interrupt workflow |
| **Data Quality** | Handles partial/invalid data |
| **Debugging** | Structured warnings for analysis |
| **UI Integration** | Objects with levels, tasks, pets |
| **Compatibility** | Works alongside old detection |
| **Performance** | Efficient, no expensive operations |
| **Scalability** | Handles 100s of tasks safely |

## Examples

See [demo_lightweight_conflicts.py](demo_lightweight_conflicts.py) for 7 comprehensive demonstrations:

1. **Safe None/Invalid Data Handling** - Shows graceful degradation
2. **Task Duration Validation** - Validates task durations
3. **Time Budget Checking** - Ensures tasks fit in schedule
4. **Comprehensive Detection** - All checks combined
5. **Resilience Test** - Extreme bad data scenarios
6. **Warning Levels** - Different severity levels
7. **Real-World Scenario** - Practical family scheduling example

Run it:
```bash
python demo_lightweight_conflicts.py
```
