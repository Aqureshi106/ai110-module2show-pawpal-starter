# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

For the initial UML design, I would have a class related to the user information regarding the pet info and basic owner. Then, another class added would be the addition and modification of tasks. Lastly, I would also add a class regarding the daily schedule generation which would require the previously described classes.

- What classes did you include, and what responsibilities did you assign to each?

Five classes are included in the UML design. The Owner class stores basic owner details, available time, and care preferences. The Pet class stores specific information like name and species regarding pets. The Task class represents each care activity, including title, duration, and priority. The TaskManager class's responsibility is to add, edit, and list tasks. Lastly, the DailyScheduleGenerator class utilizes owner constraints, pet context, and task data to generate a daily schedule and provide the rationale of its selection.

**b. Design changes**

- Did your design change during implementation?

Yes, the design did change during implementation.

- If yes, describe at least one change and why you made it.

Adding a unique id to each Task along with updating edit_task to utilize that id rather than relying on an undefined identifier or position; this change was made in order for the task updates to be consistent and prevent unintentionally editing a task.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?

It considers the time budget, soft ordering, due and completion state, conflict detection, and data validity and duplication checks.

- How did you decide which constraints mattered most?

Time availability was the most important as if total scheduled time exceeds what the owner could do, the schedule would fail in reality. The tasks that are most essential would be prioritized so the main tasks could be conducted before minor tasks.  Next would be the conflict and quality checking in order to prevent invalid durations and duplicates. Lastly would be preference as once important activities are met, then preference should be given with scheduling.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.

A tradeoff is that the scheduler uses a greedy strategy as it schedules tasks in a fixed order until the time runs out rather than solving for the best combination.

- Why is that tradeoff reasonable for this scenario?

The tradeoff is reasonable as the project needs a scheduler that is simple to understand, fast to access, and reliable to everyday pet-care planning, not a perfect optimizer; a greedy approach provides clear predictable behavior, simpler to implement and test to produce practical schedules under real time limits.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
