# AI Learning Log — CampusFlow Sprint

## Fellow: Engineer 1 (wib3)

### Interaction #1 — Error Handling Strategy: Custom Exceptions vs. Structured Error Return Values
* **Problem:** Understanding the concrete architectural trade-offs between raising custom exceptions versus returning structured error values (such as tuples or result dictionaries) for data validation in a multi-module CLI app.
* **My initial understanding:** I thought returning a dictionary like `{"success": False, "error": "msg"}` or a tuple `(None, "msg")` might be simpler because it avoids needing `try...except` blocks.
* **Prompt to AI:** "What are the key architectural differences and trade-offs between custom exceptions and structured error objects (such as tuples or result dictionaries) in Python? Specifically, how do they differ in terms of call-site boilerplate, unittest assertions, and the risk of silent bugs in a multi-module CLI application?"
* **Useful AI guidance:** AI provided an in-depth breakdown of the trade-offs:
  1. **Control flow & call-site boilerplate:** Structured errors require every caller at every layer to explicitly unpack and check `if not result['success']: return result`. If any intermediate function forgets to check, execution proceeds with invalid/None data. In contrast, exceptions naturally bubble up across function boundaries until caught by the top-level CLI or test handler.
  2. **Risk of silent failures:** Structured errors rely entirely on discipline; forgetting an error check leads to subtle downstream bugs (e.g. `TypeError: 'NoneType' object is not subscriptable`). Exceptions fail fast and halt immediately at the point of invalidity.
  3. **Testing ergonomics:** With structured errors, unit tests must assert both the dictionary keys and error values manually (`self.assertFalse(res["success"])`). With custom exceptions, Python's `unittest` provides idiomatic assertions: `with self.assertRaises(ValidationError):` and `self.assertRaisesRegex(...)`.
  4. **Performance:** Exceptions have a minor overhead when raised, but in an interactive CLI / helpdesk application with discrete user actions, this overhead is nanoseconds and irrelevant compared to safety and code clarity.
* **My independent experiment/test:** Implemented both patterns in a standalone script:
  - Pattern A (Structured return): A function returned `(None, "Invalid users")`. I simulated a caller function that forgot to check the error tuple and immediately tried to access `ticket["id"]`, triggering an unhandled `TypeError`.
  - Pattern B (Custom exception): Raised `ValidationError("Invalid users")`. The failure was caught cleanly at the caller's outer handler, and `unittest` cleanly verified it with `with self.assertRaises(ValidationError):`.
* **Verification source or result:** Verified against Python standard library idioms (PEP 3151 and official `unittest` documentation). Confirmed in test run that custom exceptions prevent silent state propagation and yield much cleaner test assertions.
* **Decision:** Accepted custom domain exceptions (`CampusFlowError`, `ValidationError`, `TicketNotFoundError`, `InvalidTransitionError`). Rejected structured error tuples/dicts because they invite silent propagation bugs across team modules.
* **Related file/commit:** `docs/design-decisions.md`, `campusflow/exceptions.py`.
* **What I can now explain without AI:** Custom exceptions invert the burden of error propagation: the developer doesn't have to write defensive error-forwarding boilerplate in every intermediate layer. Instead, errors halt bad state mutations instantly and route directly to user-facing boundaries. Structured errors are useful in languages without exception support (C, Go) or performance-critical loops, but in Python business applications, custom exceptions provide superior safety and cleaner tests.


---

### Interaction #2 — Priority Engine Rule Ordering and Boundary Evaluation
*(To be completed during implementation)*

---

### Interaction #3 — ID Generation and Safe Persistence Sequencing
*(To be completed during implementation)*

---

## Fellow: Engineer 2 (Team B)

These entries document the actual AI-assisted implementation and review in this
chat. Tests described below were executed by the assistant in the local workspace.
Personal understanding and independently run experiments remain for Engineer 2
to complete truthfully; these entries do not yet demonstrate all individual
learning requirements.

### Interaction #1 — Validation Before Mutation and Ticket Lifecycle
* **Problem:** Implement Issue #2 assignment and status transitions without changing stored tickets when an operation is invalid.
* **My initial understanding:** To be completed by Engineer 2 in their own words.
* **Prompt to AI:** "solve the team B part and let me review it"
* **Useful AI guidance:** Keep business logic separate from interactive input. Look up the ticket, validate the requested operation, then mutate it. Require an assignee before starting work and use a separate explicit reopen operation for resolved tickets.
* **My independent experiment/test:** Pending Engineer 2's own prediction and execution. Assistant verification used deep copies to compare tickets before and after rejected operations.
* **Verification source or result:** The local unittest run passed all 18 tests, including unassigned transitions, unknown IDs, blank staff names, skipped/backward transitions, and resolved-ticket locking.
* **Decision:** The original generated implementation raised `ValueError` before mutation. Interaction #4 records its correction to the shared domain exception hierarchy.
* **Related file/commit:** `campusflow/workflow.py`, `tests/test_workflow.py`; Issue #2.
* **What I can now explain without AI:** To be completed by Engineer 2 after explaining validation order and explicit reopening.

---

### Interaction #2 — Priority Sorting and Numeric Ticket IDs
* **Problem:** Order the queue by critical, high, medium, low and use earlier numeric ticket IDs to break ties.
* **My initial understanding:** To be completed by Engineer 2 in their own words.
* **Prompt to AI:** The original Team B implementation request above included queue ordering from the engineering guide.
* **Useful AI guidance:** Sort with a tuple containing a priority rank and the integer portion of the ticket ID. Return a new sorted list rather than reorder the stored collection.
* **My independent experiment/test:** Pending Engineer 2's own prediction and execution. Assistant verification tested all four priorities and tied IDs T002, T010 and T1000.
* **Verification source or result:** Queue tests passed with T002 before T010 before T1000, and confirmed that sorting leaves the stored list unchanged.
* **Decision:** The implementation uses numeric ID sorting. A string-only tie-break would incorrectly place T1000 before T999; this alternative was not adopted.
* **Related file/commit:** `campusflow/reports.py`, `tests/test_reports.py`.
* **What I can now explain without AI:** To be completed by Engineer 2 after explaining tuple sorting and numeric conversion.

---

### Interaction #3 — Comparing Issue Acceptance Criteria with the Guide
* **Problem:** Check whether Team B meets both the guide and Issue #2, especially the queue's definition.
* **My initial understanding:** To be completed by Engineer 2 in their own words.
* **Prompt to AI:** "analyze the instruction againe if my team b implemantation match what they want"
* **Useful AI guidance:** Compare each criterion with implementation and test evidence. The guide specifies an open-ticket queue, while the issue says unresolved tickets, which could also include in-progress tickets.
* **My independent experiment/test:** Pending Engineer 2's own verification. The assistant reread the supplied guide, inspected workflow/report code, and reran `python3 -m unittest discover -s tests -v`.
* **Verification source or result:** All 18 local tests passed: 11 workflow and 7 queue/report tests. The queue test explicitly excludes in-progress and resolved tickets. This does not verify the remote branch or integrated main.
* **Decision:** Qualified the earlier claim that Team B was ready: functionality matches the guide, but Issue #2 queue wording needs partner agreement. Retain open-only behavior while requesting clarification; no issue edit or partner agreement is claimed.
* **Related file/commit:** `docs/design-decisions.md`, `docs/team-b-review.md`, `tests/test_reports.py`; Issue #2.
* **What I can now explain without AI:** To be completed by Engineer 2 after explaining the wording difference and why passing tests alone does not prove integrated compliance.

---

### Interaction #4 — Critical Correction: Aligning AI-Generated Errors with the Shared Design
* **Problem:** The AI-generated Team B workflow used generic `ValueError`, while Engineer 1's shared design specifies custom exceptions derived from `CampusFlowError`. A CLI catching only `CampusFlowError` would fail to handle Team B's expected user errors.
* **My initial understanding:** Engineer 2 must add their actual initial understanding; it was not established in this conversation.
* **Prompt to AI:** "handle it you can reference the designe decision for more idea"
* **Useful AI guidance:** A function can pass isolated tests while violating a shared error contract. Match the exception hierarchy so the integrated CLI can catch errors from both engineers consistently.
* **My independent experiment/test:** Not yet claimed. The assistant reproduced an unknown-ID operation before editing: `assign_ticket([], "T999", "Ada")` raised `ValueError`. The assistant then changed workflow errors and added `test_errors_match_shared_cli_exception_contract`. Engineer 2 should predict and rerun the checks below, then record their observed result.
* **Verification source or result:** Engineer 1's `docs/design-decisions.md`, sections 3 and 4.3, specifies `CampusFlowError`, `ValidationError`, `TicketNotFoundError` and `InvalidTransitionError`. The assistant ran `python3 -m unittest discover -s tests -v`: all 19 local tests passed, including the new exception-contract test. `python3 demo_team_b.py` also completed successfully. No remote or integrated-main verification is claimed.
* **Decision (Critical Improvement / Correction):** Corrected the AI-generated `ValueError` approach. Unknown/invalid ticket IDs now raise `TicketNotFoundError`; invalid names/status values raise `ValidationError`; forbidden transitions, resolved edits and invalid reopening raise `InvalidTransitionError`. All inherit from `CampusFlowError`. Updated tests and demo handlers to use the shared hierarchy. Validation still occurs before mutation.
* **Related file/commit:** `campusflow/exceptions.py`, `campusflow/workflow.py`, `tests/test_workflow.py`, `demo_team_b.py`, `docs/design-decisions.md`. Local changes only; no commit or PR approval claimed.
* **Explanation to study:** Catching a base exception catches its subclasses. Generic `ValueError` is outside the team's `CampusFlowError` hierarchy, so the planned CLI handler would miss it. Domain exceptions preserve one shared handler while letting tests distinguish missing tickets, invalid inputs and illegal transitions.
* **What I can now explain without AI:** Engineer 2 must write their own explanation after running the experiment; the explanation above is AI guidance, not a personal statement.

#### Engineer 2's independent verification

Before running, predict which exception each operation raises and whether the
outer `CampusFlowError` handler catches it. Run from the project root:

```sh
python3 -m unittest discover -s tests -p test_workflow.py -v
python3 demo_team_b.py
```

Inspect `test_errors_match_shared_cli_exception_contract`: it checks missing IDs,
blank staff names, invalid status values and an unassigned transition, verifies
that every error derives from `CampusFlowError`, and confirms unchanged tickets.
Record your actual output and explain why the original `ValueError` advice needed
correction. This provides a real correction to verify; assistant execution alone
does not satisfy the guide's independent learning requirement.

#### Observed results — assisted verification, 12 October 2026

Executed by the assistant during Engineer 2's requested verification session:

```text
python3 -m unittest discover -s tests -p test_workflow.py -v
Ran 12 tests in 0.021s
OK
```

The exception-contract test passed for unknown IDs, blank staff names, invalid
status values and starting an unassigned ticket. It confirmed the expected
domain exception type, membership in the `CampusFlowError` hierarchy and no
ticket mutation after rejection.

`python3 demo_team_b.py` exited successfully. Its observed output showed:
- T002 (critical) appeared before T001 (low).
- Starting unassigned T002 was rejected with a clear assignment message.
- Assigning and resolving T002 produced a report with total 2, open 1 and resolved 1.
- Reassigning resolved T002 was rejected.
- Explicitly reopening T002 allowed reassignment to Bola and left status open.

#### Explanation of the correction

Python matches an `except` clause using the exception's class and its base
classes. `ValueError` and `CampusFlowError` both inherit from `Exception`, but
`ValueError` does not inherit from `CampusFlowError`. Sharing `Exception` as a
parent does not make one exception a subclass of the other. Consequently,
`except CampusFlowError` misses the original `ValueError`, allowing it to escape
the planned CLI handler.

The corrected `TicketNotFoundError`, `ValidationError` and
`InvalidTransitionError` all inherit from `CampusFlowError`. The same handler
now catches these expected workflow errors, while tests can still distinguish
their specific causes. This corrects a real integration flaw in the original
AI-generated implementation.

This explanation was drafted by the assistant from the verified implementation;
it is not attributed as Engineer 2's independently written reflection.

