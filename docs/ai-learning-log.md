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
