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

### Interaction #2 — Critical Type Evaluation: Guarding Positive Integers Against Python's Bool/Float Subtyping
* **Problem:** How to rigorously validate `affected_users` to strictly satisfy the rule: "must be a positive integer (not zero, a negative number, a decimal, or text)".
* **My initial understanding:** I thought using `isinstance(x, int) and x > 0` or casting `int(x)` would be sufficient.
* **Prompt to AI:** "How can I validate that a variable is strictly a positive integer in Python without accepting booleans, floats, or negative numbers?"
* **Useful AI guidance:** AI initially suggested checking `isinstance(val, int) and val > 0`, or converting with `int(val)`.
* **My independent experiment/test:** Ran isolated experiments in Python:
  ```python
  isinstance(True, int)   # evaluates to True! (bool is a subclass of int in Python)
  int(3.9)                # returns 3 (silently truncates decimals without error)
  ```
  The experiment proved that naive checks suggested by AI had critical flaws:
  1. Passing `True` would bypass `isinstance(val, int)` and treat `True` as `1` user!
  2. Passing a float like `3.9` into `int()` would truncate it to `3` without rejecting the decimal.
* **Verification source or result:** Verified against Python data model reference (`issubclass(bool, int)` is `True`). Wrote automated tests in `tests/test_tickets.py`: `test_reject_boolean_affected_users` and `test_reject_decimal_affected_users`. Both confirmed the vulnerability and verified the fix.
* **Decision (Critical Improvement / Correction):** Rejected the naive AI suggestion. Improved the validation logic by placing explicit defensive guards:
  ```python
  if isinstance(affected_users, bool):
      raise ValidationError("affected_users must be a positive integer.")
  elif isinstance(affected_users, float):
      raise ValidationError("affected_users must be a positive integer (not a decimal).")
  ```
* **Related file/commit:** `campusflow/tickets.py` (`validate_ticket_input`), `tests/test_tickets.py`.
* **What I can now explain without AI:** In Python, boolean values are an exact subtype of integer (`issubclass(bool, int) is True`). Therefore, `isinstance(True, int)` returns `True`. Any domain validation requiring integer purity must explicitly check for `bool` before `int`. Furthermore, casting floats directly via `int()` is lossy and hides invalid input rather than rejecting it.

---

### Interaction #3 — Stateless Deterministic ID Generation Across Persistence Restarts
* **Problem:** Ensuring unique, sequential ticket IDs (`T001`, `T002`, ...) that remain unique across restarts and reloads without generating duplicate keys.
* **My initial understanding:** I considered using a module-level global variable `counter = 0` that increments on every ticket creation.
* **Prompt to AI:** "What are the risks of using an in-memory counter for auto-incrementing IDs in a CLI app with JSON persistence, and what is a stateless alternative?"
* **Useful AI guidance:** AI explained that volatile module counters reset to `0` whenever the application terminates. When reloaded from a JSON file with existing tickets, a naive counter starts over at `T001`, causing ID collisions and corrupted records. AI recommended deriving the next ID directly from the loaded ticket dataset.
* **My independent experiment/test:** Built `generate_next_id(tickets)` that inspects all existing ticket IDs, parses the numeric portion (`int(id[1:])`), finds `max_num`, and formats the next ID as `f"T{max_num + 1:03d}"`. Tested with an existing list containing gaps `[{"id": "T001"}, {"id": "T009"}]`.
* **Verification source or result:** Verified with unit test `test_id_generation_with_existing_gaps` in `tests/test_tickets.py`. The function cleanly produced `T010` without conflicts or reliance on global state.
* **Decision:** Accepted the stateless collection-derived ID generator. Rejected global mutable state counters.
* **Related file/commit:** `campusflow/tickets.py` (`generate_next_id`), `tests/test_tickets.py`.
* **What I can now explain without AI:** Global in-memory state is an anti-pattern in persistent applications because process lifecycles and data lifecycles do not match. Deriving IDs from the existing collection makes ID generation idempotent, gap-tolerant, and completely safe across application restarts.

