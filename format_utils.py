"""Formatting utilities for PawPal+ CLI output.

Provides emoji badges, ANSI color helpers (via colorama), and tabulate-based
table printers used by main.py demo functions.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from tabulate import tabulate

try:
    import colorama
    from colorama import Fore, Style

    colorama.init(autoreset=True)
    _COLORS = True
except ImportError:
    _COLORS = False

if TYPE_CHECKING:
    from pawpal_system import ConflictWarning, Owner, ScheduledTask, Task

# ---------------------------------------------------------------------------
# Emoji lookup tables
# ---------------------------------------------------------------------------

PRIORITY_EMOJI: Dict[str, str] = {
    "high": "🔴",
    "medium": "🟡",
    "low": "🟢",
}

FREQUENCY_EMOJI: Dict[str, str] = {
    "daily": "📅",
    "weekly": "📆",
    "monthly": "🗓️",
    "as-needed": "✨",
}

SPECIES_EMOJI: Dict[str, str] = {
    "dog": "🐶",
    "cat": "🐱",
    "rabbit": "🐰",
    "bird": "🐦",
    "fish": "🐟",
    "hamster": "🐹",
    "other": "🐾",
}

STATUS_EMOJI: Dict[bool, str] = {
    True: "✅",
    False: "⏳",
}

CONFLICT_EMOJI: Dict[str, str] = {
    "critical": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
}

# ---------------------------------------------------------------------------
# Color helpers (degrade gracefully when colorama is absent)
# ---------------------------------------------------------------------------

def _c(text: str, *codes: str) -> str:
    """Wrap text in ANSI codes if colorama is available, otherwise return plain text."""
    if not _COLORS:
        return text
    return "".join(codes) + text + Style.RESET_ALL


def red(text: str) -> str:
    return _c(text, Fore.RED) if _COLORS else text


def yellow(text: str) -> str:
    return _c(text, Fore.YELLOW) if _COLORS else text


def green(text: str) -> str:
    return _c(text, Fore.GREEN) if _COLORS else text


def cyan(text: str) -> str:
    return _c(text, Fore.CYAN) if _COLORS else text


def bold(text: str) -> str:
    return _c(text, Style.BRIGHT) if _COLORS else text


def dim(text: str) -> str:
    return _c(text, Style.DIM) if _COLORS else text


# ---------------------------------------------------------------------------
# Badge helpers — one-liner labels that combine emoji + text
# ---------------------------------------------------------------------------

def priority_badge(priority_value: str) -> str:
    """Return an emoji + uppercase label for a priority value string."""
    key = priority_value.lower()
    emoji = PRIORITY_EMOJI.get(key, "⬜")
    label = key.upper()
    if key == "high":
        return red(f"{emoji} {label}")
    if key == "medium":
        return yellow(f"{emoji} {label}")
    return green(f"{emoji} {label}")


def frequency_badge(frequency: str) -> str:
    """Return an emoji + frequency label."""
    key = frequency.lower()
    emoji = FREQUENCY_EMOJI.get(key, "🔁")
    return f"{emoji} {frequency}"


def species_badge(species: str) -> str:
    """Return an emoji + species label."""
    key = species.lower()
    emoji = SPECIES_EMOJI.get(key, "🐾")
    return f"{emoji} {species}"


def status_badge(completed: bool) -> str:
    """Return an emoji + status label."""
    emoji = STATUS_EMOJI.get(completed, "•")
    label = "Done" if completed else "Pending"
    return dim(f"{emoji} {label}") if completed else f"{emoji} {label}"


def conflict_badge(level: str) -> str:
    """Return an emoji + severity label."""
    emoji = CONFLICT_EMOJI.get(level, "•")
    label = level.upper()
    if level == "critical":
        return red(f"{emoji} {label}")
    if level == "warning":
        return yellow(f"{emoji} {label}")
    return cyan(f"{emoji} {label}")


# ---------------------------------------------------------------------------
# Row formatters
# ---------------------------------------------------------------------------

def _task_to_row(task: "Task") -> Dict[str, Any]:
    """Convert a Task to a display-ready dict for tabulate."""
    from pawpal_system import PriorityLevel

    pet_label = f"{SPECIES_EMOJI.get((task.pet_name or '').lower(), '')} {task.pet_name or '—'}".strip()
    return {
        "Status": status_badge(task.completed),
        "Priority": priority_badge(task.priority.value),
        "Pet": pet_label,
        "Task": bold(task.description) if not task.completed else dim(task.description),
        "Duration": f"{task.time_minutes} min",
        "Frequency": frequency_badge(task.frequency),
    }


def _scheduled_to_row(
    task: "Task",
    start: int,
    urgency_score: Optional[int] = None,
) -> Dict[str, Any]:
    """Convert a scheduled Task to a display-ready row."""
    end = start + task.time_minutes
    row: Dict[str, Any] = {
        "Time": f"{start:02d}–{end:02d} min",
        "Priority": priority_badge(task.priority.value),
        "Pet": f"{SPECIES_EMOJI.get((task.pet_name or '').lower(), '')} {task.pet_name or '—'}".strip(),
        "Task": bold(task.description),
        "Duration": f"{task.time_minutes} min",
        "Frequency": frequency_badge(task.frequency),
    }
    if urgency_score is not None:
        row["Urgency"] = str(urgency_score)
    return row


def _deferred_to_row(task: "Task") -> Dict[str, Any]:
    """Convert a deferred Task to a display-ready row."""
    return {
        "Priority": priority_badge(task.priority.value),
        "Pet": f"{SPECIES_EMOJI.get((task.pet_name or '').lower(), '')} {task.pet_name or '—'}".strip(),
        "Task": dim(task.description),
        "Duration": f"{task.time_minutes} min",
        "Frequency": frequency_badge(task.frequency),
    }


# ---------------------------------------------------------------------------
# Section header printer
# ---------------------------------------------------------------------------

TABLE_FMT = "rounded_outline"


def print_section_header(title: str, width: int = 68) -> None:
    """Print a visually distinct section header using ASCII-safe characters."""
    bar = "=" * width
    print()
    print(bold(cyan(bar)))
    print(bold(cyan(f"  {title}")))
    print(bold(cyan(bar)))


# ---------------------------------------------------------------------------
# Table printers
# ---------------------------------------------------------------------------

def print_task_table(tasks: "List[Task]", title: str = "Tasks") -> None:
    """Print a formatted task table using tabulate."""
    print_section_header(title)
    if not tasks:
        print(dim("  (no tasks)"))
        return
    rows = [_task_to_row(t) for t in tasks]
    print(tabulate(rows, headers="keys", tablefmt=TABLE_FMT))


def print_schedule_table(
    scheduled: "List[Task]",
    deferred: "List[Task]",
    budget: int,
    title: str = "Today's Schedule",
    urgency_scores: Optional[Dict[str, int]] = None,
) -> None:
    """Print a formatted schedule table using tabulate."""
    print_section_header(title)

    if not scheduled and not deferred:
        print(dim("  (no tasks to schedule)"))
        return

    if scheduled:
        used = sum(t.time_minutes for t in scheduled)
        pct = int(used / budget * 100) if budget > 0 else 0
        budget_label = green(f"{used}/{budget} min ({pct}% of budget)") if pct <= 100 else red(f"{used}/{budget} min")
        print(f"\n  {bold('Scheduled')}  ·  {budget_label}")

        rows = []
        cur = 0
        for t in scheduled:
            score = urgency_scores.get(t.id) if urgency_scores else None
            rows.append(_scheduled_to_row(t, cur, score))
            cur += t.time_minutes
        print(tabulate(rows, headers="keys", tablefmt=TABLE_FMT))

    if deferred:
        deferred_min = sum(t.time_minutes for t in deferred)
        print(f"\n  {bold(yellow('Deferred'))}  ·  {yellow(f'{len(deferred)} task(s), {deferred_min} min not scheduled')}")
        rows = [_deferred_to_row(t) for t in deferred]
        print(tabulate(rows, headers="keys", tablefmt=TABLE_FMT))


def print_conflicts(conflicts: "List[str]", lightweight: bool = False) -> None:
    """Print a formatted conflicts section."""
    if not conflicts:
        return
    label = "Lightweight Conflict Warnings" if lightweight else "Scheduling Conflicts"
    print_section_header(label)
    rows = [{"#": i + 1, "Message": c} for i, c in enumerate(conflicts)]
    print(tabulate(rows, headers="keys", tablefmt=TABLE_FMT))


def print_conflict_warnings(warnings: "List[ConflictWarning]") -> None:
    """Print structured ConflictWarning objects as a tabulate table."""
    if not warnings:
        return
    print_section_header("Conflict Warnings (Lightweight Detector)")
    rows = [
        {
            "Severity": conflict_badge(w.level),
            "Message": w.message,
            "Pets": ", ".join(w.pet_names) if w.pet_names else "—",
        }
        for w in warnings
    ]
    print(tabulate(rows, headers="keys", tablefmt=TABLE_FMT))


def print_owner_summary(owner: "Owner") -> None:
    """Print a compact owner + pets summary."""
    print_section_header(f"Owner: {owner.name}")
    rows = [
        {
            "Pet": species_badge(p.species),
            "Name": bold(p.name),
            "Tasks": len(p.tasks),
            "Pending": sum(1 for t in p.tasks if not t.completed),
            "Total Time": f"{sum(t.time_minutes for t in p.tasks if not t.completed)} min",
        }
        for p in owner.pets
    ]
    print(tabulate(rows, headers="keys", tablefmt=TABLE_FMT))
    budget_note = f"  Daily budget: {bold(str(owner.time_available_minutes))} min"
    print(budget_note)
