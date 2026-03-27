# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

For the initial UML design, I would have a class related to the user information regarding the pet info and basic owner. Another class handles adding and modifying tasks. Lastly, I would also add a class regarding the daily schedule generation which would require the previously described classes.

- What classes did you include, and what responsibilities did you assign to each?

Five classes are included in the UML design. The Owner class stores basic owner details, available time, and care preferences. The Pet class stores specific information like pet name and species. The Task class represents each care activity, including title, duration, and priority. The TaskManager class's responsibility is to add, edit, and list tasks. Lastly, the DailyScheduleGenerator class utilizes owner constraints, pet context, and task data to generate a daily schedule and provide the rationale of its selection.

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

This tradeoff is reasonable because the scheduler prioritizes simplicity, speed, and reliability over optimality; a greedy approach provides clear predictable behavior, simpler to implement and test to produce practical schedules under real time limits.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?

With the AI tools, it greatly assisted me with debugging the code to find errors, along with thinking of the algorithmic design, and refactoring the code to ensure the code to be more efficient and readable. Also, it assisted me with writing pytests to know the code is reliable.

- What kinds of prompts or questions were most helpful?

I utilized prompts such as reviewing the code to ensure if the logic fulfills the requirements that the project asks. I also asked how the algorithmic design of the app should be written and why the design would be the best in terms of the scenario of the project.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

I had asked Copilot with regards to describing the priority of the algorithmic design of the scheduler, it was describing it directly based on a task priority field but I thought of describing it based on due and completion status, frequency order and duration, so I had to utilize a different prompt.

- How did you evaluate or verify what the AI suggested?

As I had to make sure the suggestion would accomplish what the directions of the project asked, I then utilized the pytests to see if the code accurately works and if not, I had to review the logic and algorithmic design to see if an error exists.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?

The task state management, sorting and filtering, scheduling logic, task recurrence, time-budget conflict detection, time preference conflict detection, scheduled time overlap detection, sequential task handling, and lightweight conflict detection.

- Why were these tests important?

These tests are crucial as it determines if each key behavior functions correctly such as task list operations, completion status, order preservation, tracking occurrences, availability of time, overlaps within a certain pet, task window overlap between different pets, confirmation of non-overlapping adjacent tasks, and provide warnings that doesn't cause the application to crash on malformed data.

**b. Confidence**

- How confident are you that your scheduler works correctly?

Given that the demo worked with the basic operations, I am confident that the scheduler will work correctly in terms of the app and logic as the pytests passed, many cases were handled and the design is constructed to promote efficiency.

- What edge cases would you test next if you had more time?

The case of very large task sets in order to check the performence of the scheduler as well as correctness. Another case would be null/missing values such as null due dates and pets with no tasks assigned. Also, empty or extreme time budgets which a circumstance where scheduling can occur in only 1 minute available.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I am satisfied with how the project's design was organized including Copilot's ability to understand the prompts I utilized based on the directions of the project to ensure the efficiency and functionality of the application.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

If given another iteration, perhaps I would look to test edge cases that weren't considered or redesign the algorithmic structure that could make improve the application compared to what was constructed.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

With regards to takeaway from designing systems with the utilization of artificial intelligence is to realize that it is critical for the prompts to be clear and precise for the articicial intelligence to interpret what is being asked to provide accurate suggestions as systems are complex and being brief can only do so much, details are vital.
