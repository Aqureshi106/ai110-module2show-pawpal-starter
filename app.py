import streamlit as st
from pawpal_system import Owner, Pet, Scheduler, Task


def get_or_create_owner(owner_name: str) -> Owner:
    """Reuse the Owner object from session state, or create it once."""
    if "owner" not in st.session_state:
        st.session_state.owner = Owner(name=owner_name, time_available_minutes=60)
    else:
        st.session_state.owner.name = owner_name
    return st.session_state.owner

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

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
species = st.selectbox("Species", ["dog", "cat", "other"])

owner = get_or_create_owner(owner_name)
owner.time_available_minutes = int(time_available)
scheduler = Scheduler()
st.caption(f"Session owner in vault: {owner.name}")

pet_exists = any(p.name == pet_name for p in owner.pets)
if st.button("Add pet to owner"):
    if not pet_exists:
        owner.add_pet(Pet(name=pet_name, species=species))
        st.success(f"Added pet '{pet_name}' to session owner.")
    else:
        st.info(f"Pet '{pet_name}' already exists in session owner.")

if owner.pets:
    st.write("Owner pets:")
    st.table([{"name": p.name, "species": p.species} for p in owner.pets])

st.markdown("### Tasks")
st.caption("Add a task to a selected pet using your class methods.")

pet_names = [pet.name for pet in owner.pets]
selected_pet_name = st.selectbox(
    "Assign task to pet",
    pet_names,
    disabled=not bool(pet_names),
)

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    frequency = st.selectbox("Frequency", ["daily", "weekly", "monthly", "as-needed"], index=0)

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
                )
            )
            st.success(f"Added task '{task_title}' to {target_pet.name}.")

all_tasks = owner.get_all_tasks()
if all_tasks:
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        filter_pet = st.selectbox("Filter by pet", ["All"] + pet_names)
    with filter_col2:
        filter_status = st.selectbox("Filter by status", ["all", "pending", "completed"])
    with filter_col3:
        sort_mode = st.selectbox("Sort by time", ["shortest-first", "longest-first"])

    selected_pet = None if filter_pet == "All" else filter_pet
    selected_status = None
    if filter_status == "pending":
        selected_status = False
    elif filter_status == "completed":
        selected_status = True

    filtered_tasks = scheduler.filter_tasks(owner, pet_name=selected_pet, completed=selected_status)
    filtered_tasks = scheduler.sort_by_time(
        filtered_tasks,
        ascending=(sort_mode == "shortest-first"),
    )

    st.write("Current tasks:")
    st.table(
        [
            {
                "pet": task.pet_name,
                "task": task.description,
                "duration_minutes": task.time_minutes,
                "frequency": task.frequency,
                "completed": task.completed,
            }
            for task in filtered_tasks
        ]
    )
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button calls Scheduler to organize and plan today's tasks.")

if st.button("Generate schedule"):
    plan = scheduler.build_daily_schedule(owner)
    organized = plan["scheduled"]
    deferred = plan["deferred"]
    conflicts = plan["conflicts"]

    if not organized:
        st.info("No tasks available to schedule.")
    else:
        scheduled_rows = []
        current_minute = 0

        for task in organized:
            scheduled_rows.append(
                {
                    "time_window": f"{current_minute:02d}-{current_minute + task.time_minutes:02d}",
                    "pet": task.pet_name,
                    "task": task.description,
                    "duration": task.time_minutes,
                    "frequency": task.frequency,
                }
            )
            current_minute += task.time_minutes

        deferred_rows = [
            {
                "pet": task.pet_name,
                "task": task.description,
                "duration": task.time_minutes,
                "frequency": task.frequency,
            }
            for task in deferred
        ]

        st.write("Today's Schedule")
        if scheduled_rows:
            st.table(scheduled_rows)
        else:
            st.info("No tasks fit in the available time.")

        if deferred_rows:
            st.write("Deferred tasks")
            st.table(deferred_rows)

        if conflicts:
            st.write("Scheduling conflicts")
            for conflict in conflicts:
                st.warning(conflict)
