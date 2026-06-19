# AI Interactions Log

This document records every meaningful AI-assisted session during this project,
following the format: files modified, what I asked the agent to do, what it
completed, and any manual corrections I made.

---

## Session 1 — Core System Design and Scheduling

**Date:** Early project phase

**What I asked:**
Help me design a pet care scheduling system with classes for Owner, Pet, and Task,
and implement a daily scheduling algorithm that respects a time budget.

**What the agent completed:**
- Defined dataclasses: `Owner`, `Pet`, `Task`, `ScheduledTask`, `DailyPlan`
- Implemented `Scheduler.organize_tasks` with multi-key sort (completion → frequency → duration)
- Implemented `Scheduler.build_daily_schedule` using a greedy fill algorithm
- Added `Scheduler.filter_tasks` and `Scheduler.sort_by_time`

**Files modified:** `pawpal_system.py`

**Manual corrections:**
- The agent suggested using a priority field (low/medium/high enum) as the primary
  sort key. I overrode this in favour of due-state + frequency rank, because frequency
  reflects real-world urgency better than a subjective priority label.
- Added `PriorityLevel` enum as a stub (kept for possible future use) but wired the
  sort to frequency instead.

---

## Session 2 — Conflict Detection

**Date:** Mid project phase

**What I asked:**
Add time-overlap conflict detection for tasks that have preferred start times, and
a "lightweight" variant that never throws exceptions so it is safe to call from the UI.

**What the agent completed:**
- Implemented `Scheduler.detect_conflicts` (budget overrun, non-positive durations,
  duplicate recurring signatures, preferred-time overlaps same-pet and cross-pet)
- Implemented `Scheduler.detect_scheduled_time_conflicts` for already-scheduled tasks
- Added `LightweightConflictDetector` class with per-check safe methods and
  `detect_all_conflicts` that never raises
- Added `ConflictWarning` dataclass with severity levels and emoji rendering

**Files modified:** `pawpal_system.py`

**Manual corrections:**
- Reduced verbosity of the lightweight detector's docstrings; the agent wrote
  multi-paragraph explanations that I trimmed to single-line summaries.
- Verified all 33 automated tests passed before accepting the changes.

---

## Session 3 — Sorting, Filtering, and Recurrence

**Date:** Mid project phase

**What I asked:**
Add sorting by time (ascending/descending), filtering by pet/completion status, and
recurring task logic so daily/weekly tasks auto-spawn a next occurrence when marked complete.

**What the agent completed:**
- `Scheduler.sort_by_time` and `sort_tasks_by_time` compatibility alias
- `Scheduler.filter_tasks` with pet_name and completed filters
- `Scheduler.is_task_due` with frequency-interval and date-based due logic
- `Scheduler.mark_task_complete` with `_create_next_occurrence` helper
- Full test coverage in `tests/test_pawpal.py`

**Files modified:** `pawpal_system.py`, `tests/test_pawpal.py`

**Manual corrections:** None — the implementation matched requirements on first pass.

---

## Session 4 — Streamlit UI

**Date:** Late project phase

**What I asked:**
Wire the backend into `app.py` with controls to add pets and tasks, filter/sort the
task list, generate a schedule, and display conflict warnings.

**What the agent completed:**
- Owner/pet creation with session state persistence
- Task input form with pet selector, title, duration, and frequency
- Filter controls (by pet, by status) and sort toggle (shortest/longest first)
- Schedule builder with `build_daily_schedule`, deferred task display, and conflict
  warning panels using `detect_conflicts_lightweight`

**Files modified:** `app.py`

**Manual corrections:**
- Moved the `render_lightweight_warning` helper above `st.set_page_config` to avoid
  a Streamlit ordering warning.
- Changed `st.write("Current tasks:")` row-count caption to an `st.success` with
  total-minutes summary for better visual feedback.

---

## Session 5 — Stretch Feature: Urgency-Weighted Smart Prioritization

**Date:** Final project phase

### Agent Workflow

**What I asked:**
Add a third algorithmic capability — urgency-weighted prioritization — that is
meaningfully distinct from the existing `sort_by_time` (duration-only) and
`organize_tasks` (static frequency rank). The new algorithm should score tasks
dynamically using multiple factors and reorder the schedule accordingly.

Specifically:
1. Add `Scheduler.compute_urgency_score(task, day_index, current_date)` — a static
   method returning an integer score based on four weighted factors.
2. Add `Scheduler.sort_by_urgency_score(tasks, day_index, current_date)` — sorts
   tasks by that score, highest first.
3. Add `Scheduler.build_urgency_prioritized_schedule(owner, day_index, pet_name,
   current_date)` — identical flow to `build_daily_schedule` but uses urgency order
   instead of frequency rank, and returns an `urgency_scores` dict in the result.
4. Update `app.py`:
   - Add "urgency (highest first)" option to the sort dropdown; show an
     `urgency_score` column in the task table when this mode is active.
   - Add a "Use urgency-weighted prioritization" checkbox in the schedule builder
     section that switches between `build_daily_schedule` and
     `build_urgency_prioritized_schedule`.
   - Label the generated schedule "Today's Schedule (Urgency-Prioritized)" when the
     checkbox is checked.
   - Show `urgency_score` column in the scheduled-tasks table when urgency mode is on.

**What the agent completed:**

All four items above were implemented as requested:

- `compute_urgency_score` in `pawpal_system.py` (lines ~648–698):
  - Overdue factor: 10 pts/day past `due_date`, capped at 50
  - Recency factor: days-since-completion ÷ frequency interval × 15, capped at 30;
    never-completed tasks get a flat 20-pt bonus
  - Frequency baseline: daily=20, weekly=12, monthly=6, as-needed=3
  - Duration bonus: `max(0, 10 - time_minutes // 10)` — rewards short tasks
  - Completed tasks always return 0

- `sort_by_urgency_score` in `pawpal_system.py` — wraps `compute_urgency_score` in
  a `sorted(..., reverse=True)` call

- `build_urgency_prioritized_schedule` in `pawpal_system.py`:
  - Filters and scores all due, incomplete tasks
  - Greedy fill in descending urgency order
  - Converts to `ScheduledTask` objects with the urgency score in the `reason` field
  - Returns `urgency_scores` dict alongside `scheduled`, `deferred`, `conflicts`

- `app.py` updates:
  - Sort dropdown now has three options; urgency path calls `sort_by_urgency_score`
    and appends `urgency_score` key to each row dict
  - `use_urgency` checkbox added before "Generate schedule" button
  - Schedule builder branches on `use_urgency` to call the appropriate method
  - `urgency_score` column appears in scheduled-tasks table when urgency mode is on
  - Schedule section header changes to reflect the active mode

**Files modified:**
- `pawpal_system.py` — added ~110 lines (three new methods on `Scheduler`)
- `app.py` — updated sort dropdown, task table, and schedule builder (~25 line diff)

**Manual corrections:**
- None required. The agent's implementation matched the specification exactly.
  Verified by reading both files after the edits to confirm all changes landed
  correctly and no existing behaviour was disturbed.

---

### Why urgency-weighted prioritization is a genuine algorithmic advance

The existing capabilities sort or filter but do not *score*:

| Capability | Key | Dynamic? |
|---|---|---|
| `sort_by_time` | `task.time_minutes` | No |
| `organize_tasks` | `(completed, freq_rank, duration)` | No |
| **`compute_urgency_score`** | overdue days + recency ratio + freq baseline + duration bonus | **Yes** |

A monthly task that is 15 days overdue will score higher than a daily task completed
5 minutes ago, even though the daily task has a higher static frequency rank. The
score changes every day as `due_date` and `last_completed_day` shift, making it a
genuinely time-aware prioritisation rather than a fixed ordering rule.

---

## Session 6 — Data Persistence (JSON save / load)

**Date:** Final project phase

**What I asked:**
Add data persistence so PawPal+ remembers pets and tasks between application runs.
Specifically:
1. Add `to_dict()` / `from_dict()` methods to `Task`, `Pet`, and `Owner` so each
   object can be serialized to and reconstructed from a plain Python dict.
2. Add module-level `save_to_json(owner, filepath)` and `load_from_json(filepath)`
   functions at the bottom of `pawpal_system.py`. No third-party library —
   use the standard-library `json` module plus a custom dict conversion.
3. Handle `date` fields by storing them as ISO-8601 strings in JSON and parsing
   them back with `date.fromisoformat()` on load. Return `None` from
   `load_from_json` when the file does not exist (not an exception).
4. Update `app.py` to:
   - Try loading from `data.json` the first time a browser session initializes
     (inside `get_or_create_owner`).
   - Auto-save after every "Add pet" and "Add task" mutation.
   - Add a sidebar showing whether a save file exists and a "Clear saved data"
     button that deletes the file and resets the session.
   - Show a persistence note next to the owner caption.
5. Add a **Data Persistence** section to `README.md` explaining the workflow,
   the serialization design, and which files were changed.

**What the agent completed:**

All five items above were implemented as requested:

- `pawpal_system.py`:
  - Added `import json` and `from pathlib import Path` to the top-level imports.
  - `Task.to_dict()` serializes all nine fields; `due_date` stored as ISO string or
    `None`. `Task.from_dict()` reconstructs with original `id` preserved and
    `date.fromisoformat()` for the date field.
  - `Pet.to_dict()` serializes name, species, and nested task list.
    `Pet.from_dict()` calls `Task.from_dict()` for each saved task.
  - `Owner.to_dict()` serializes name, time budget, preferences, and nested pet list.
    `Owner.from_dict()` calls `Pet.from_dict()` for each saved pet.
  - `save_to_json(owner, filepath="data.json")` — opens file for writing and calls
    `json.dump(owner.to_dict(), fh, indent=2)`.
  - `load_from_json(filepath="data.json")` — returns `None` if file is absent;
    otherwise reads JSON and returns `Owner.from_dict(data)`.

- `app.py`:
  - Imported `os`, `load_from_json`, `save_to_json`.
  - `DATA_FILE` set to an absolute path via `os.path.dirname(__file__)` so the file
    always lands in the project directory regardless of working directory.
  - `get_or_create_owner` now tries `load_from_json(DATA_FILE)` on first session
    init; falls back to a fresh `Owner` when no file exists.
  - `save_to_json(owner, DATA_FILE)` called immediately after pet and task additions;
    success messages updated to confirm save.
  - Sidebar added with file-presence check, status message, and "Clear saved data"
    button (deletes file, clears session state, calls `st.rerun()`).
  - Owner caption updated to show "· data.json loaded" or "· no saved data".

- `README.md`:
  - New **Data Persistence** section added before **Features**, covering the
    workflow diagram, serialization table, public API example, and files-modified
    table.

**Files modified:**
- `pawpal_system.py` — imports, `to_dict`/`from_dict` on 3 classes, 2 module-level functions (~90 lines added)
- `app.py` — import changes, `get_or_create_owner` update, auto-save calls, sidebar (~25 lines changed)
- `README.md` — new Data Persistence section (~55 lines added)

**Manual corrections:**
- None. All assertions in the round-trip smoke test passed on first run:
  - All nine `Task` fields survived save → load, including `due_date` ISO conversion.
  - `load_from_json` on a missing path returned `None` as specified.
  - All 33 existing tests continued to pass with no regressions.

---

## Session 7 — Priority-Based Scheduling

**Date:** Final project phase

**What I asked:**
Add a `Priority` level (Low / Medium / High) to `Task` and update `Scheduler` to sort by
priority first, then by frequency rank, then by duration. Also add CLI output examples
to README.md demonstrating the enhanced scheduling logic.

Specifically:
1. Add `priority: PriorityLevel = PriorityLevel.MEDIUM` to `Task` (after `frequency`,
   before `completed`). The `PriorityLevel` enum already exists as a `str` enum stub —
   just wire it in.
2. Add `priority_order` class dict to `Scheduler` (`HIGH=0, MEDIUM=1, LOW=2`).
3. Update `organize_tasks` sort key from `(completed, freq_rank, duration)` to
   `(completed, priority_rank, freq_rank, duration)`.
4. Update `DailyScheduleGenerator.generate_schedule` to match the same sort key.
5. Add a priority bonus to `compute_urgency_score` (HIGH=+25, MEDIUM=+10, LOW=+0).
6. Update `Task.to_dict()` to include `"priority": self.priority.value` and
   `Task.from_dict()` to parse `PriorityLevel(data.get("priority", "medium"))`.
7. Update `app.py`: import `PriorityLevel`; add a 4-column task form with a Priority
   selector; show a `priority` column (upper-cased enum value) in the task list table,
   scheduled-tasks table, and deferred-tasks table.
8. Add `print_priority_scheduling_demo()` to `main.py` and call it from `main()`.
9. Update `README.md` with a new **Priority-Based Scheduling** section containing a
   table of the example tasks, the actual CLI output captured from running the demo,
   a key-observation note, a priority/urgency-score table, and a files-modified table.

**What the agent completed:**

All nine items above were implemented as requested:

- `Task.priority` field added between `frequency` and `completed`. Default is
  `PriorityLevel.MEDIUM` so all existing test code (which omits the argument) gets
  MEDIUM automatically — confirmed 33/33 tests still pass.
- `Scheduler.priority_order` class dict added after `frequency_order`.
- `organize_tasks` sort lambda updated to `(completed, priority_rank, freq_rank, duration)`.
- `DailyScheduleGenerator.generate_schedule` sort lambda updated to match.
- `compute_urgency_score` extended with a `priority_bonus` dict lookup.
- `Task.to_dict` / `Task.from_dict` updated for the `priority` field.
- `app.py`: `PriorityLevel` imported; task form extended to four columns with a
  Priority selectbox ("High", "Medium", "Low", default "Medium"); `PRIORITY_MAP` dict
  converts label strings to `PriorityLevel` values; `priority` column added to all
  three task tables (task list, scheduled, deferred).
- `main.py`: `PriorityLevel` imported; `print_priority_scheduling_demo()` added and
  called from `__main__`. Demo shows insertion order → `sort_by_time` → `organize_tasks`
  → `build_daily_schedule`, making it visually clear that priority changes which tasks
  enter the 60-minute budget.
- `README.md`: **Priority-Based Scheduling** section added with worked example, captured
  CLI output, key observation, urgency bonus table, and files-modified table.

**Files modified:**
- `pawpal_system.py` — `Task` field, `Scheduler.priority_order`, three sort-key updates, urgency bonus, serialization (~25 lines changed)
- `app.py` — `PriorityLevel` import, 4-column form, priority column in 3 tables (~20 lines changed)
- `main.py` — `PriorityLevel` import, `print_priority_scheduling_demo()` function (~35 lines added)
- `README.md` — new Priority-Based Scheduling section (~65 lines added)

**Manual corrections:**
- None. Verified by running the full test suite (33/33 pass) and running the demo
  script to capture actual CLI output for the README — the output matched expectations
  exactly on first run.

---

## Session 8 — Professional UI and Output Formatting

**Date:** Final project phase

**What I asked:**
Add user-friendly output to PawPal+ CLI and Streamlit UI:
1. Create a new `format_utils.py` module containing:
   - Emoji lookup dicts (`PRIORITY_EMOJI`, `FREQUENCY_EMOJI`, `SPECIES_EMOJI`,
     `STATUS_EMOJI`, `CONFLICT_EMOJI`).
   - Color helper functions (`red`, `yellow`, `green`, `cyan`, `bold`, `dim`) wrapping
     colorama with a plain-text fallback when colorama is unavailable.
   - Badge helper functions (`priority_badge`, `frequency_badge`, `species_badge`,
     `status_badge`, `conflict_badge`) that combine emoji + text + color into a
     single label string.
   - Table printers using `tabulate` with `rounded_outline` style:
     `print_task_table`, `print_schedule_table` (with optional urgency column),
     `print_conflicts`, `print_conflict_warnings`, `print_owner_summary`.
   - `print_section_header` using ASCII `=` dividers (not Unicode box-drawing chars,
     for Windows cp1252 compatibility).
2. Rewrite `main.py` demo functions to use `format_utils` for all output, replacing
   raw `print` loops. Add a UTF-8 stdout shim at the top.
3. Update `app.py`:
   - Import emoji dicts from `format_utils`.
   - Species selector uses `format_func` to show emoji labels.
   - Pet summary table adds species emoji, task count, pending count.
   - Task table: `status` column (✅/⏳ + label), `priority` column (🔴/🟡/🟢 +
     level), `pet` column (emoji + name), `frequency` column (calendar emoji +
     recurrence).
   - Schedule and deferred tables use the same emoji-enriched columns.
   - Sidebar: adds emoji legend for priority / status / frequency, and a 💾 emoji
     to the persistence status indicator.
4. Add `tabulate>=0.9.0` and `colorama>=0.4.6` to `requirements.txt`.
5. Add a **Professional UI and Output Formatting** section to `README.md` documenting
   the emoji reference table, library choices, `format_utils` public API, a CLI
   output sample, Streamlit UI changes, files modified, and the Windows encoding note.

**What the agent completed:**

All five items above were implemented as requested:

- `format_utils.py` (new, ~290 lines):
  - All five emoji dicts; six color helpers using colorama with graceful fallback.
  - Five badge helpers returning colored emoji + text strings.
  - `_task_to_row`, `_scheduled_to_row`, `_deferred_to_row` — internal row converters.
  - `print_task_table`, `print_schedule_table`, `print_conflicts`,
    `print_conflict_warnings`, `print_owner_summary` — tabulate printers.
  - `print_section_header` — ASCII `=` dividers (safe on cp1252 terminals).

- `main.py` (rewritten):
  - UTF-8 stdout shim at the top (`sys.stdout.reconfigure(encoding='utf-8')`).
  - Six demo functions (`demo_sorting_and_filtering`, `demo_schedule`,
    `demo_conflict_detection`, `demo_priority_scheduling`, `demo_urgency_schedule`)
    all using format_utils printers.
  - Fixed urgency demo: removed `last_completed_day=0` so Daily meds is due and
    appears in the schedule with urgency score 75.

- `app.py`:
  - `format_utils` emoji dicts imported.
  - Species selector: expanded to 7 options with emoji format_func.
  - Pet table: 4 columns (emoji+name, species, task count, pending count).
  - Task table: 6 emoji-enriched columns (status, priority, pet, task, duration, freq).
  - Schedule/deferred tables: emoji-enriched priority, pet, frequency columns.
  - Sidebar: 💾 emoji in header/status, legend for all emoji codes.
  - Owner caption updated to include 🐾 emoji.

- `requirements.txt`: `tabulate>=0.9.0` and `colorama>=0.4.6` added.
- `README.md`: **Professional UI and Output Formatting** section added before Data
  Persistence, with full documentation of libraries, API, CLI sample, and files table.

**Files modified:**
- `format_utils.py` — new file, ~290 lines
- `main.py` — rewritten (~200 lines, replaced raw print loops with format_utils calls)
- `app.py` — emoji dicts import, species selector, 4 table updates, sidebar legend (~40 lines changed)
- `requirements.txt` — 2 lines added
- `README.md` — new formatting section (~90 lines added)

**Manual corrections:**
- Section header initially used Unicode box-drawing characters (╭─╮) which caused a
  `UnicodeEncodeError` via colorama's cp1252 Windows conversion layer. Fixed by
  replacing with ASCII `=` dividers and adding the UTF-8 stdout shim in main.py.
- Urgency demo was missing "Daily meds" because `last_completed_day=0` meant the
  task was not due on day_index=0. Fixed by removing that argument (default None →
  always due), which also makes the demo more instructive.
- All 33 existing tests continued to pass after all changes.

---

## Prompt Comparison: Next-Occurrence Scheduling for Overdue Recurring Tasks

### Background

`Scheduler._create_next_occurrence` computes when a recurring daily or weekly task
should next be due after the owner marks it complete. The current implementation is:

```python
offset_days = 1 if frequency == "daily" else 7
next_due_date = current_date + timedelta(days=offset_days)
```

This always anchors the next due date to **today + N days**, regardless of whether
the task was completed on time or weeks late. That raises a real design question:

> If a weekly task was due on Monday and the owner completes it on Friday (4 days
> late), should the next occurrence be due *next Friday* (7 days from today) or
> *next Monday* (7 days from the original due date)?
>
> And what if the task is 3 weeks overdue — should the system quietly skip the
> missed cycles, or schedule them all at once?

This is a bounded, concrete algorithmic question with real user-experience
tradeoffs, making it a good candidate for a model comparison.

---

### Prompt sent to both models

```
Context: PawPal+ is a pet care scheduling app. The Task dataclass has these fields:
  description: str, time_minutes: int, frequency: str ("daily" or "weekly"),
  due_date: Optional[date], last_completed_day: Optional[int]

Here is the current _create_next_occurrence method:

  def _create_next_occurrence(self, task, current_day, current_date):
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

Problem: if a weekly task was due on 2026-06-01 but was only completed on
2026-06-15 (two weeks late), the current code schedules the next occurrence for
2026-06-22 — two weeks after the original due date, rather than 2026-06-08.

Should the next due date be anchored to today (rolling schedule) or to the
original due date (fixed cadence)? Please implement whichever approach you
think is better and explain your reasoning.
```

---

### Model 1: Claude Sonnet (used in this project)

**Approach proposed:** Rolling schedule — anchor to completion date

Claude's argument was that anchoring to the original due date creates a hidden
"catch-up debt" problem. If the task was missed many times, every occurrence
would be due immediately or in the past. For a pet care app where real-world
conditions (illness, travel, schedule disruption) cause unavoidable lateness,
this produces an unworkable backlog.

**Proposed implementation:**

```python
def _create_next_occurrence(self, task, current_day, current_date):
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
```

This is identical to the existing code — Claude validated the current approach
rather than changing it, and explained why.

**What was useful:**
- Clear justification grounded in user behavior ("lateness accumulates debt").
- The simplicity keeps the contract predictable: complete a task → it comes back
  in exactly N days, every time.
- Integrates cleanly with `is_task_due` because `due_date` is always a future date
  relative to when the task was completed.

**What was flawed:**
- No mention of the tradeoff: users who care about strict cadence (e.g., weekly
  grooming every Sunday) lose schedule alignment entirely if they complete a task
  on a different day. A dog groomed on Friday instead of Sunday will permanently
  shift to a Friday schedule with no way to recover.
- Did not propose any middle-ground option (e.g., a max-drift guard).

---

### Model 2: ChatGPT GPT-4o (comparison, consulted separately)

**Approach proposed:** Cadence-aware scheduling with drift correction

GPT-4o argued that pet care tasks often have biological or logistical reasons for
their cadence (e.g., weekly flea treatment, monthly heartworm prevention). Silently
drifting away from the intended schedule reduces the system's practical value.

**Proposed implementation:**

```python
def _create_next_occurrence(self, task, current_day, current_date):
    frequency = task.frequency.lower()
    if frequency not in {"daily", "weekly"}:
        return None

    offset_days = 1 if frequency == "daily" else 7

    # Anchor to original due date if it exists and drift is within one full interval.
    # Beyond one interval, reset to today to avoid scheduling in the past.
    if task.due_date is not None:
        cadence_next = task.due_date + timedelta(days=offset_days)
        if cadence_next > current_date:
            next_due_date = cadence_next          # within drift window: preserve cadence
        else:
            next_due_date = current_date + timedelta(days=offset_days)  # too late: reset
    else:
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
```

**What was useful:**
- The drift-correction logic is genuinely clever: if you complete the task only
  one day late, the next occurrence stays on the original schedule; if you're
  very late, it resets cleanly to avoid scheduling in the past.
- The `task.due_date is not None` guard handles the case of newly created tasks
  with no prior anchor.
- Better for use cases where the schedule cadence has medical or biological
  significance (flea treatment every Monday, heartworm pill first of the month).

**What was flawed:**
- Added a conditional branch without tests, leaving the behavior of the
  `cadence_next > current_date` boundary underspecified. What happens if the
  task is completed exactly on its due date (cadence_next == due_date + interval)?
  This works correctly only by accident.
- The function now behaves differently depending on whether `task.due_date` is
  set — a hidden mode switch that would be easy to miss during debugging.
- No handling for tasks created without an original `due_date` (new tasks added by
  the user from the UI default to `due_date=None`), so the drift correction silently
  degrades to rolling behavior for half the task population without explanation.
- More complex code means more surface area for the test suite to cover; GPT-4o
  did not suggest corresponding test cases.

---

### Final decision: retain rolling schedule (Claude's approach)

The current `_create_next_occurrence` implementation was kept unchanged. The
reasoning:

1. **User mental model.** "I just did this task, it comes back in N days" is
   simpler and more predictable than "it comes back at the next cadence-aligned
   date, unless that's already passed, in which case it comes back in N days."
   Cognitive load matters for a daily-use app.

2. **Backlog prevention.** With the drift-correction approach, a user who
   completes a monthly task that is 3 weeks late will get the next occurrence
   due in 1 week (`due_date + 30 days` is only 9 days away). This is arguably
   more disruptive than just giving the owner a fresh 30-day window.

3. **Test coverage.** The rolling approach produces deterministic outputs:
   `next_due_date = completion_date + N`. The cadence-aware approach produces
   different outputs depending on when the task was originally due, which
   requires a broader test matrix to cover the boundary between "within drift
   window" and "reset" branches.

4. **Data dependency.** The drift-correction approach only works when `due_date`
   is set on the task. Tasks added from the Streamlit UI default to `due_date=None`
   and would silently receive rolling behavior anyway, making the complexity
   partially wasted.

**One insight retained from GPT-4o's response:** the boundary condition analysis
(what happens if `cadence_next == current_date` exactly) was useful. It highlighted
that `_create_next_occurrence` should be clearly documented as rolling-only so
future developers do not accidentally assume cadence-preservation. A docstring
clarification was added to the method.

**Partial adoption:** if a future version of PawPal+ needs strict cadence support
(e.g., medication reminders), GPT-4o's `cadence_next > current_date` guard is a
clean starting point — provided it is gated on `task.due_date is not None` and
covered by tests for both the within-drift and past-due branches.
