# Scheduler Time Conflict Detection - Enhancement Summary

## Overview
The Scheduler has been extended to detect if two tasks for the same pet (or different pets) are scheduled at the same time. This enhancement includes both preferred-time conflict detection and actual scheduled-time overlap detection.

## New Methods & Features

### 1. `_has_time_overlap(start1, end1, start2, end2) -> bool` (Static Method)
**Purpose:** Helper method to determine if two time windows overlap.

**Parameters:**
- `start1`, `end1`: Start and end times of first window (in minutes)
- `start2`, `end2`: Start and end times of second window (in minutes)

**Returns:** `True` if windows overlap, `False` otherwise

**Example:**
```python
scheduler = Scheduler()
scheduler._has_time_overlap(0, 10, 5, 15)  # Returns True (overlap 5-10)
scheduler._has_time_overlap(0, 10, 10, 20)  # Returns False (sequential)
```

### 2. `detect_scheduled_time_conflicts(scheduled_tasks: List[ScheduledTask]) -> List[str]`
**Purpose:** Detect overlapping time windows in already-scheduled tasks.

**Parameters:**
- `scheduled_tasks`: List of `ScheduledTask` objects with start/end times

**Returns:** List of conflict messages describing overlapping tasks

**Features:**
- Detects overlaps between any two scheduled tasks
- Works for same-pet and different-pet scenarios
- Identifies which tasks overlap and their time ranges

**Example:**
```python
scheduler = Scheduler()
scheduled = [
    ScheduledTask(task_id="1", task_title="Walk", start_minute=0, end_minute=20, reason=""),
    ScheduledTask(task_id="2", task_title="Play", start_minute=15, end_minute=30, reason=""),
]
conflicts = scheduler.detect_scheduled_time_conflicts(scheduled)
# Returns: ["Time conflict detected: 'Walk' (0-20 min) overlaps with 'Play' (15-30 min)."]
```

### 3. Enhanced `detect_conflicts()` Method
**Improvements:**
- Extended preferred-time overlap detection to work across **different pets** (not just same pet)
- Now detects cross-pet scheduling conflicts
- Maintains all original conflict detection (duplicate tasks, time budget, invalid durations)

**New Conflict Types Detected:**
- Same-pet preferred-time overlaps: `"Preferred-time overlap for pet 'X': 'Task1' and 'Task2'."`
- Different-pet preferred-time overlaps: `"Time conflict across different pets: 'Task1' for PetA (...) overlaps with 'Task2' for PetB (...)."`

## Integration with Existing Code

### `build_daily_schedule()` Method
The method now:
1. Builds the schedule as before (sequential task placement)
2. Creates `ScheduledTask` objects from the scheduled tasks
3. Calls both `detect_conflicts()` and `detect_scheduled_time_conflicts()`
4. Returns combined conflict list in the result

**Usage:**
```python
scheduler = Scheduler()
schedule = scheduler.build_daily_schedule(owner)
print(schedule["conflicts"])  # Contains all detected conflicts
```

## Test Coverage

Six new tests have been added to verify the functionality:

1. **`test_detect_same_pet_preferred_time_conflicts`** - Detects overlaps for the same pet
2. **`test_detect_different_pet_preferred_time_conflicts`** - Detects overlaps across different pets
3. **`test_detect_scheduled_task_time_overlaps_same_pet`** - Detects scheduled time overlaps
4. **`test_detect_scheduled_task_time_overlaps_different_pets`** - Detects cross-pet scheduled overlaps
5. **`test_no_overlap_when_tasks_are_sequential`** - Validates sequential tasks don't trigger false positives
6. **`test_has_time_overlap_helper`** - Tests the time overlap detection logic

**All 16 tests pass** (10 existing + 6 new)

## Usage Examples

### Example 1: Detect Same-Pet Conflicts
```python
from pawpal_system import Owner, Pet, Scheduler, Task

owner = Owner(name="Alex", time_available_minutes=120)
mochi = Pet(name="Mochi", species="dog")
owner.add_pet(mochi)

# Add tasks with overlapping preferred times
mochi.add_task(Task(
    description="Meds",
    time_minutes=5,
    frequency="daily",
    preferred_start_minute=0
))
mochi.add_task(Task(
    description="Breakfast",
    time_minutes=10,
    frequency="daily",
    preferred_start_minute=3  # Overlaps with meds!
))

scheduler = Scheduler()
conflicts = scheduler.detect_conflicts(mochi.list_tasks(), available_minutes=120)
# Output: "Preferred-time overlap for pet 'Mochi': 'Meds' and 'Breakfast'."
```

### Example 2: Detect Different-Pet Conflicts
```python
owner = Owner(name="Alex", time_available_minutes=120)
mochi = Pet(name="Mochi", species="dog")
luna = Pet(name="Luna", species="cat")
owner.add_pet(mochi)
owner.add_pet(luna)

# Add tasks for different pets with overlapping preferred times
mochi.add_task(Task(
    description="Feeding",
    time_minutes=10,
    frequency="daily",
    preferred_start_minute=10
))
luna.add_task(Task(
    description="Feeding",
    time_minutes=15,
    frequency="daily",
    preferred_start_minute=15  # Overlaps with Mochi's feeding!
))

scheduler = Scheduler()
all_tasks = owner.get_all_tasks()
conflicts = scheduler.detect_conflicts(all_tasks, available_minutes=120)
# Output includes: "Time conflict across different pets: 'Feeding' for Mochi (10-20 min) 
# overlaps with 'Feeding' for Luna (15-30 min)."
```

### Example 3: Detect Scheduled Task Overlaps
```python
from pawpal_system import ScheduledTask

scheduler = Scheduler()
scheduled_tasks = [
    ScheduledTask(task_id="1", task_title="Mochi Walk", start_minute=0, 
                  end_minute=20, reason="Morning"),
    ScheduledTask(task_id="2", task_title="Luna Groom", start_minute=15, 
                  end_minute=35, reason="Grooming"),
]

conflicts = scheduler.detect_scheduled_time_conflicts(scheduled_tasks)
# Output: "Time conflict detected: 'Mochi Walk' (0-20 min) overlaps with 
# 'Luna Groom' (15-35 min)."
```

## Implementation Details

### Time Overlap Logic
Two time windows overlap if:
- `start1 < end2` AND `start2 < end1`

This correctly handles:
- Partial overlaps: `[0, 10]` and `[5, 15]` → overlaps
- Sequential tasks: `[0, 10]` and `[10, 20]` → no overlap
- Contained windows: `[10, 20]` and `[0, 30]` → overlaps
- Identical windows: `[10, 20]` and `[10, 20]` → overlaps

### Conflict Detection Strategy
1. **Preferred-Time Conflicts:** Detected during task planning (before scheduling)
2. **Scheduled-Time Conflicts:** Detected after tasks are placed in the timeline
3. **Cross-Pet Detection:** All conflicts checked against all pets, not just within pets

## Backward Compatibility

✅ **Fully backward compatible** - All existing tests pass without modification.
- New methods added without changing existing signatures
- Enhanced `detect_conflicts()` still handles all previous conflict types
- `build_daily_schedule()` returns the same structure with additional conflict information

## Files Modified

1. **`pawpal_system.py`**
   - Added `_has_time_overlap()` static method
   - Added `detect_scheduled_time_conflicts()` method
   - Enhanced `detect_conflicts()` method to detect cross-pet overlaps
   - Updated `build_daily_schedule()` to call both conflict detection methods

2. **`tests/test_pawpal.py`**
   - Added 6 new test functions for time conflict detection
   - All tests passing (16/16)

3. **`demo_time_conflicts.py`** (New)
   - Demonstration script showing all conflict detection scenarios
   - Includes 5 different demo functions
