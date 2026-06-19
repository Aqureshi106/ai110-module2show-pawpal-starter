# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Professional UI and Output Formatting

PawPal+ uses **emoji badges**, **ANSI color highlighting**, and **`tabulate`-based structured tables** throughout all CLI output. All formatting logic lives in [`format_utils.py`](format_utils.py) so it is reusable and testable independently of the scheduling logic.

### Emoji reference

| Symbol | Meaning |
|---|---|
| 🔴 HIGH / 🟡 MEDIUM / 🟢 LOW | Priority levels |
| ✅ Done / ⏳ Pending | Task completion status |
| 📅 daily / 📆 weekly / 🗓️ monthly / ✨ as-needed | Recurrence frequency |
| 🐶 dog / 🐱 cat / 🐰 rabbit / 🐦 bird / 🐟 fish / 🐹 hamster / 🐾 other | Pet species |
| ⚠️ WARNING / ❌ CRITICAL / ℹ️ INFO | Conflict severity levels |
| 💾 | Data persistence status |

### Libraries used

| Library | Purpose | Version |
|---|---|---|
| `tabulate` | Structured Unicode tables with `rounded_outline` style | ≥ 0.9.0 |
| `colorama` | Cross-platform ANSI color codes (RED for HIGH, YELLOW for MEDIUM, GREEN for LOW, CYAN for headers) | ≥ 0.4.6 |

### format_utils.py — public API

```python
from format_utils import (
    priority_badge,     # "🔴 HIGH"  (colored)
    frequency_badge,    # "📅 daily"
    species_badge,      # "🐶 dog"
    status_badge,       # "✅ Done" / "⏳ Pending"
    conflict_badge,     # "⚠️ WARNING"  (colored)
    print_task_table,       # tabulate task list with Status/Priority/Pet/Task/Duration/Frequency
    print_schedule_table,   # tabulate schedule with Time/Priority/Pet/Task/Duration + optional Urgency
    print_conflicts,        # tabulate plain conflict message list
    print_conflict_warnings,# tabulate structured ConflictWarning objects
    print_owner_summary,    # tabulate per-pet summary with species emoji
    print_section_header,   # ANSI-colored ASCII section divider
)
```

### CLI output sample

```
====================================================================
  Daily Schedule  ·  Jordan  ·  60 min budget
====================================================================

  Scheduled  ·  50/60 min (83% of budget)
╭───────────┬────────────┬───────┬──────────────────┬────────────┬─────────────╮
│ Time      │ Priority   │ Pet   │ Task             │ Duration   │ Frequency   │
├───────────┼────────────┼───────┼──────────────────┼────────────┼─────────────┤
│ 00–10 min │ 🟡 MEDIUM   │ Mochi │ Feed breakfast   │ 10 min     │ 📅 daily     │
│ 10–25 min │ 🟡 MEDIUM   │ Luna  │ Clean litter box │ 15 min     │ 📅 daily     │
│ 25–50 min │ 🟡 MEDIUM   │ Mochi │ Morning walk     │ 25 min     │ 📅 daily     │
╰───────────┴────────────┴───────┴──────────────────┴────────────┴─────────────╯

  Deferred  ·  1 task(s), 20 min not scheduled
╭────────────┬───────┬──────────────┬────────────┬─────────────╮
│ Priority   │ Pet   │ Task         │ Duration   │ Frequency   │
├────────────┼───────┼──────────────┼────────────┼─────────────┤
│ 🟡 MEDIUM   │ Luna  │ Play session │ 20 min     │ 📆 weekly    │
╰────────────┴───────┴──────────────┴────────────┴─────────────╯

====================================================================
  Conflict Warnings (Lightweight Detector)
====================================================================
╭────────────┬─────────────────────────────────────────────────────────────────────┬────────╮
│ Severity   │ Message                                                             │ Pets   │
├────────────┼─────────────────────────────────────────────────────────────────────┼────────┤
│ ⚠️ WARNING │ Total task time (70 min) exceeds available time (60 min). 10 min…  │ —      │
╰────────────┴─────────────────────────────────────────────────────────────────────┴────────╯
```

### Streamlit UI enhancements

- **Species selector** uses `format_func` to show `🐶 dog`, `🐱 cat`, etc.
- **Pet summary table** includes species emoji, task count, and pending count.
- **Task table** columns include `status` (✅/⏳ + label), `priority` (🔴/🟡/🟢 + level), `pet` (species emoji + name), and `frequency` (calendar emoji + recurrence).
- **Schedule and deferred tables** include the same emoji-enriched priority and frequency columns.
- **Sidebar** displays a legend for all emoji codes and a 💾 persistence status indicator.

### Files modified for formatting

| File | Change |
|---|---|
| `format_utils.py` | **New file** — all emoji dicts, badge helpers, color wrappers, tabulate table printers |
| `main.py` | Replaced all raw `print` loops with `format_utils` functions; added UTF-8 stdout shim |
| `app.py` | Imported emoji dicts; emoji-enriched species selector, pet table, task table, schedule tables, sidebar legend |
| `requirements.txt` | Added `tabulate>=0.9.0` and `colorama>=0.4.6` |

### Notes on Windows terminal compatibility

The UTF-8 stdout shim at the top of `main.py` ensures emojis render correctly:
```python
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
```
Section headers use ASCII `=` dividers (not Unicode box-drawing characters) for maximum cross-platform compatibility. Colorama provides ANSI color support for Windows terminals.

## Data Persistence

PawPal+ automatically saves and restores all owner, pet, and task data between runs using a `data.json` file stored in the project directory.

### How it works

Every time you add a pet or a task the app calls `save_to_json` and writes the complete state to `data.json`. The next time the app starts, `load_from_json` reads that file and restores the session — you pick up exactly where you left off.

```
Add pet / Add task
        │
        ▼
save_to_json(owner, "data.json")   ← called automatically after each mutation
        │
        ▼
data.json on disk

App restart
        │
        ▼
load_from_json("data.json")        ← called once per browser session on first load
        │
        ▼
Owner (with pets and tasks) restored in Streamlit session state
```

The sidebar shows whether a saved file exists. A **Clear saved data** button deletes `data.json` and resets the session if you want to start fresh.

### Serialization design

No third-party library is required — persistence is handled entirely by custom `to_dict` / `from_dict` methods on each dataclass:

| Class | What it persists |
|---|---|
| `Task.to_dict()` | All fields including `due_date` as ISO-8601 string |
| `Task.from_dict()` | Reconstructs task, parses date string back to `date` object |
| `Pet.to_dict()` | Name, species, and list of serialized tasks |
| `Pet.from_dict()` | Reconstructs pet and calls `Task.from_dict` for each task |
| `Owner.to_dict()` | Name, time budget, preferences, and list of serialized pets |
| `Owner.from_dict()` | Reconstructs owner and calls `Pet.from_dict` for each pet |

Module-level functions provide the public API:

```python
from pawpal_system import save_to_json, load_from_json

save_to_json(owner)            # writes data.json
owner = load_from_json()       # returns Owner or None if file missing
```

### Files modified for persistence

| File | Change |
|---|---|
| `pawpal_system.py` | Added `import json`, `from pathlib import Path`; added `to_dict` / `from_dict` to `Owner`, `Pet`, `Task`; added module-level `save_to_json` and `load_from_json` |
| `app.py` | Imported `save_to_json`, `load_from_json`; modified `get_or_create_owner` to load from file on first session; added auto-save calls after pet/task mutations; added sidebar persistence status and "Clear saved data" button |

## Priority-Based Scheduling

Every `Task` carries a `priority` field (`HIGH`, `MEDIUM`, or `LOW`, default `MEDIUM`). The scheduler sorts tasks by **priority first**, then by frequency rank, then by duration. This means a `HIGH`-priority monthly task always enters the schedule before a `LOW`-priority daily task, regardless of duration or recurrence.

### How priority changes the schedule

The example below uses a 60-minute time budget and five tasks:

| Task | Priority | Frequency | Duration |
|---|---|---|---|
| Administer eye drops | HIGH | daily | 5 min |
| Morning walk | LOW | daily | 30 min |
| Refill water bowl | MEDIUM | daily | 5 min |
| Weekly grooming | MEDIUM | weekly | 20 min |
| Vet appointment | HIGH | monthly | 45 min |

```
$ python main.py

======================================================================
PRIORITY-BASED SCHEDULING DEMO
======================================================================

Tasks (insertion order):
  Task                      Priority Frequency  Duration
  -------------------------------------------------------
  Administer eye drops      HIGH     daily          5 min
  Morning walk              LOW      daily         30 min
  Refill water bowl         MEDIUM   daily          5 min
  Weekly grooming           MEDIUM   weekly        20 min
  Vet appointment           HIGH     monthly       45 min

sort_by_time  (duration only — priority ignored):
  [HIGH  ] Administer eye drops        5 min  daily
  [MEDIUM] Refill water bowl           5 min  daily
  [MEDIUM] Weekly grooming            20 min  weekly
  [LOW   ] Morning walk               30 min  daily
  [HIGH  ] Vet appointment            45 min  monthly

organize_tasks  (priority -> frequency -> duration):
  [HIGH  ] Administer eye drops        5 min  daily
  [HIGH  ] Vet appointment            45 min  monthly
  [MEDIUM] Refill water bowl           5 min  daily
  [MEDIUM] Weekly grooming            20 min  weekly
  [LOW   ] Morning walk               30 min  daily

build_daily_schedule  (60 min budget, priority-ordered fill):
  00-05  [HIGH  ] Administer eye drops        5 min
  05-50  [HIGH  ] Vet appointment            45 min
  50-55  [MEDIUM] Refill water bowl           5 min
  Time used: 55/60 min

  Deferred (did not fit in budget):
    [MEDIUM] Weekly grooming            20 min
    [LOW   ] Morning walk               30 min
```

**Key observation:** `sort_by_time` puts the `HIGH`-priority vet appointment last (it's the longest task). `organize_tasks` and `build_daily_schedule` put it second — right after the critical daily eye drops — because priority overrides frequency rank and duration. The `LOW`-priority daily walk is deferred even though it is shorter and more frequent than the monthly vet appointment.

### Priority in `compute_urgency_score`

Priority also feeds into the urgency-weighted scheduling algorithm (see Urgency-Weighted Smart Prioritization):

| Priority | Urgency bonus added |
|---|---|
| HIGH | +25 points |
| MEDIUM | +10 points |
| LOW | +0 points |

### Files modified for priority scheduling

| File | Change |
|---|---|
| `pawpal_system.py` | Added `priority: PriorityLevel = PriorityLevel.MEDIUM` field to `Task`; added `priority_order` class dict to `Scheduler`; updated `organize_tasks` and `DailyScheduleGenerator.generate_schedule` sort keys; added priority bonus to `compute_urgency_score`; updated `to_dict` / `from_dict` |
| `app.py` | Added `PriorityLevel` import; added 4th column (Priority selector) to task form; added `priority` column to task list and schedule tables |
| `main.py` | Added `print_priority_scheduling_demo()` function demonstrating the difference between `sort_by_time`, `organize_tasks`, and `build_daily_schedule` |

## Features

Core algorithms currently implemented in PawPal+:

- Multi-key task ordering: tasks are sorted by completion state, recurrence frequency rank (`daily` -> `weekly` -> `monthly` -> `as-needed`), then duration.
- Sorting by time: standalone shortest-first or longest-first sorting by task duration.
- Recurrence-aware due logic: determines whether tasks are due based on frequency intervals (daily/weekly/monthly), completion history, and optional date-based due dates.
- Greedy daily scheduling: fills the available minute budget sequentially with ordered due tasks and defers any tasks that no longer fit.
- Time-budget conflict warnings: flags when total pending task minutes exceed the owner's available time.
- Preferred-time overlap detection: detects overlaps between preferred task windows for the same pet and across different pets.
- Scheduled-window conflict detection: pairwise overlap checks across concrete scheduled start/end windows.
- Daily/weekly recurrence spawning: when a recurring task is completed, the next occurrence is automatically created with the correct next due date.
- Duplicate recurring-task detection: identifies repeated task signatures (pet + normalized description + frequency).
- Lightweight safe conflict mode: returns structured warning objects and gracefully handles malformed/null values without crashing.

## 📸 Demo

Add your final Streamlit app screenshot to the repository as `image.png`, then it will render below:

![PawPal+ Final Streamlit App](image.png)

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Testing PawPal+

Run the full test suite with:

```bash
python -m pytest
```

Current tests cover core scheduling reliability, including task sorting correctness, filtering by pet and completion state, recurring-task due logic, next-occurrence creation for daily/weekly tasks, preferred-time and scheduled-time conflict detection (including exact duplicate time windows), and lightweight conflict handling for malformed/edge-case data.

Confidence Level: ★★★★☆ (4/5)

Reasoning For Rating: The suite is consistently passing (33/33 tests) and exercises the most important happy paths plus critical edge cases. Confidence is not 5/5 because long-term runtime behavior and broader integration/UI scenarios are not fully stress-tested.