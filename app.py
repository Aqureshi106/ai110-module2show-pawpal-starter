import os

import streamlit as st
from format_utils import FREQUENCY_EMOJI, PRIORITY_EMOJI, SPECIES_EMOJI, STATUS_EMOJI
from pawpal_system import Owner, Pet, PriorityLevel, Scheduler, Task, load_from_json, save_to_json

DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")


def get_or_create_owner(owner_name: str) -> Owner:
    """Return the session owner, loading from data.json on first run if it exists."""
    if "owner" not in st.session_state:
        loaded = load_from_json(DATA_FILE)
        st.session_state.owner = loaded if loaded is not None else Owner(
            name=owner_name, time_available_minutes=60
        )
    else:
        st.session_state.owner.name = owner_name
    return st.session_state.owner


def render_lightweight_warning(level: str, message: str) -> None:
    """Render a conflict warning with severity-aware Streamlit styling."""
    if level == "critical":
        st.error(message)
    elif level == "warning":
        st.warning(message)
    else:
        st.info(message)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

with st.sidebar:
    st.header("💾 Data Persistence")
    data_exists = os.path.isfile(DATA_FILE)
    if data_exists:
        st.success("✅ data.json found — pets and tasks will be restored on next restart.")
    else:
        st.info("ℹ️ No saved data yet. Add pets or tasks to create data.json.")

    if data_exists and st.button("🗑️ Clear saved data"):
        os.remove(DATA_FILE)
        if "owner" in st.session_state:
            del st.session_state["owner"]
        st.rerun()

    st.divider()
    st.caption("Priority key")
    st.markdown("🔴 **HIGH** · 🟡 **MEDIUM** · 🟢 **LOW**")
    st.caption("Status key")
    st.markdown("✅ Done · ⏳ Pending")
    st.caption("Frequency key")
    st.markdown("📅 daily · 📆 weekly · 🗓️ monthly · ✨ as-needed")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
time_available = st.number_input(
    "Time available today (minutes)", min_value=1, max_value=720, value=60
)
pet_name = st.text_input("Pet name", value="Mochi")
species_options = ["dog", "cat", "rabbit", "bird", "fish", "hamster", "other"]
species = st.selectbox(
    "Species",
    species_options,
    format_func=lambda s: f"{SPECIES_EMOJI.get(s, '🐾')} {s}",
)

owner = get_or_create_owner(owner_name)
owner.time_available_minutes = int(time_available)
scheduler = Scheduler()
persistence_note = " · 💾 data.json loaded" if os.path.isfile(DATA_FILE) else " · no saved data"
st.caption(f"🐾 Session owner: {owner.name}{persistence_note}")

pet_exists = any(p.name == pet_name for p in owner.pets)
if st.button("Add pet to owner"):
    if not pet_exists:
        owner.add_pet(Pet(name=pet_name, species=species))
        save_to_json(owner, DATA_FILE)
        st.success(f"Added pet '{pet_name}' to session owner. (Saved to data.json)")
    else:
        st.info(f"Pet '{pet_name}' already exists in session owner.")

if owner.pets:
    st.write("Owner pets:")
    st.table([{
        "pet": f"{SPECIES_EMOJI.get(p.species.lower(), '🐾')} {p.name}",
        "species": p.species,
        "tasks": len(p.tasks),
        "pending": sum(1 for t in p.tasks if not t.completed),
    } for p in owner.pets])

st.markdown("### Tasks")
st.caption("Add a task to a selected pet using your class methods.")

pet_names = [pet.name for pet in owner.pets]
selected_pet_name = st.selectbox(
    "Assign task to pet",
    pet_names,
    disabled=not bool(pet_names),
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    frequency = st.selectbox("Frequency", ["daily", "weekly", "monthly", "as-needed"], index=0)
with col4:
    priority_label = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)

PRIORITY_MAP = {"High": PriorityLevel.HIGH, "Medium": PriorityLevel.MEDIUM, "Low": PriorityLevel.LOW}

if st.button("Add task"):
    if not pet_names:
        st.warning("Add at least one pet before adding tasks.")
    else:
        target_pet = next((pet for pet in owner.pets if pet.name == selected_pet_name), None)
        if target_pet is None:
            st.error("Selected pet was not found.")
        else:
            target_pet.add_task(
                Task(
                    description=task_title,
                    time_minutes=int(duration),
                    frequency=frequency,
                    priority=PRIORITY_MAP[priority_label],
                )
            )
            save_to_json(owner, DATA_FILE)
            st.success(f"Added task '{task_title}' ({priority_label} priority) to {target_pet.name}. (Saved to data.json)")

all_tasks = owner.get_all_tasks()
if all_tasks:
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        filter_pet = st.selectbox("Filter by pet", ["All"] + pet_names)
    with filter_col2:
        filter_status = st.selectbox("Filter by status", ["all", "pending", "completed"])
    with filter_col3:
        sort_mode = st.selectbox(
            "Sort by",
            ["shortest-first", "longest-first", "urgency (highest first)"],
        )

    selected_pet = None if filter_pet == "All" else filter_pet
    selected_status = None
    if filter_status == "pending":
        selected_status = False
    elif filter_status == "completed":
        selected_status = True

    filtered_tasks = scheduler.filter_tasks(owner, pet_name=selected_pet, completed=selected_status)
    if sort_mode == "urgency (highest first)":
        filtered_tasks = scheduler.sort_by_urgency_score(filtered_tasks)
    else:
        filtered_tasks = scheduler.sort_tasks_by_time(
            filtered_tasks,
            ascending=(sort_mode == "shortest-first"),
        )

    show_urgency = sort_mode == "urgency (highest first)"
    task_rows = [
        {
            "status": f"{STATUS_EMOJI.get(task.completed, '•')} {'Done' if task.completed else 'Pending'}",
            "priority": f"{PRIORITY_EMOJI.get(task.priority.value, '⬜')} {task.priority.value.upper()}",
            "pet": f"{SPECIES_EMOJI.get((task.pet_name or '').lower(), '')} {task.pet_name or '—'}".strip(),
            "task": task.description,
            "duration": f"{task.time_minutes} min",
            "frequency": f"{FREQUENCY_EMOJI.get(task.frequency.lower(), '🔁')} {task.frequency}",
            **({"urgency_score": scheduler.compute_urgency_score(task)} if show_urgency else {}),
        }
        for task in filtered_tasks
    ]

    if task_rows:
        total_filtered_minutes = sum(task.time_minutes for task in filtered_tasks)
        st.success(
            f"Showing {len(task_rows)} task(s) after filtering and sorting "
            f"({total_filtered_minutes} total minutes)."
        )
        st.write("Current tasks:")
        st.table(task_rows)
    else:
        st.warning("No tasks match the current filters.")
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button calls Scheduler to organize and plan today's tasks.")

use_urgency = st.checkbox(
    "Use urgency-weighted prioritization",
    help="Scores each task by overdue status, recency, and frequency — then schedules highest-urgency tasks first.",
)

if st.button("Generate schedule"):
    if use_urgency:
        plan = scheduler.build_urgency_prioritized_schedule(owner)
    else:
        plan = scheduler.build_daily_schedule(owner)
    urgency_scores = plan.get("urgency_scores", {})
    organized = plan["scheduled"]
    deferred = plan["deferred"]
    schedule_conflicts = plan["conflicts"]
    lightweight_warnings = scheduler.detect_conflicts_lightweight(owner)

    if not organized and not deferred:
        st.info("No tasks available to schedule.")
    else:
        scheduled_rows = []
        current_minute = 0

        for task in organized:
            row = {
                "time": f"{current_minute:02d}–{current_minute + task.time_minutes:02d} min",
                "priority": f"{PRIORITY_EMOJI.get(task.priority.value, '⬜')} {task.priority.value.upper()}",
                "pet": f"{SPECIES_EMOJI.get((task.pet_name or '').lower(), '')} {task.pet_name or '—'}".strip(),
                "task": task.description,
                "duration": f"{task.time_minutes} min",
                "frequency": f"{FREQUENCY_EMOJI.get(task.frequency.lower(), '🔁')} {task.frequency}",
            }
            if use_urgency and task.id in urgency_scores:
                row["urgency"] = urgency_scores[task.id]
            scheduled_rows.append(row)
            current_minute += task.time_minutes

        sorted_deferred_tasks = scheduler.sort_tasks_by_time(deferred, ascending=True)
        deferred_rows = [
            {
                "priority": f"{PRIORITY_EMOJI.get(task.priority.value, '⬜')} {task.priority.value.upper()}",
                "pet": f"{SPECIES_EMOJI.get((task.pet_name or '').lower(), '')} {task.pet_name or '—'}".strip(),
                "task": task.description,
                "duration": f"{task.time_minutes} min",
                "frequency": f"{FREQUENCY_EMOJI.get(task.frequency.lower(), '🔁')} {task.frequency}",
            }
            for task in sorted_deferred_tasks
        ]

        schedule_label = "Today's Schedule (Urgency-Prioritized)" if use_urgency else "Today's Schedule"
        st.write(schedule_label)
        if scheduled_rows:
            scheduled_minutes = sum(task.time_minutes for task in organized)
            st.success(
                f"Scheduled {len(scheduled_rows)} task(s) within today's budget "
                f"({scheduled_minutes}/{owner.time_available_minutes} minutes used)."
            )
            st.table(scheduled_rows)
        else:
            st.info("No tasks fit in the available time.")

        if deferred_rows:
            deferred_minutes = sum(task.time_minutes for task in deferred)
            st.warning(
                f"Deferred {len(deferred_rows)} task(s) "
                f"({deferred_minutes} total minutes) due to time constraints."
            )
            st.write("Deferred tasks")
            st.table(deferred_rows)

        if schedule_conflicts:
            st.write("Scheduling conflicts")
            for conflict in schedule_conflicts:
                st.warning(conflict)

    if lightweight_warnings:
        st.write("Conflict warnings (lightweight detector)")
        for warning in lightweight_warnings:
            render_lightweight_warning(warning.level, str(warning))
