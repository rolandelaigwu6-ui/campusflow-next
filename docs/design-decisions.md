# CampusFlow — Architecture & Design Decisions

## 1. Overview & Team Ownership
CampusFlow is a Python CLI helpdesk ticket management system.

* **Engineer 1 (Wealth Ibe):**
  - F1: Ticket Creation & Input Validation (`campusflow/tickets.py`)
  - Priority Engine (Rules 1–4) (`campusflow/tickets.py`)
  - F2: List and View Tickets (`campusflow/tickets.py`)
  - Unit tests for validation, priority calculation, and ticket creation (`tests/test_tickets.py`)
* **Engineer 2 (Roland Elaigwu):**
  - F3: Staff Assignment (`campusflow/workflow.py`)
  - F4: Lifecycle Transitions (`open` -> `in_progress` -> `resolved`, reopen) (`campusflow/workflow.py`)
  - F5: Open-Ticket Work Queue (`campusflow/reports.py`)
  - F6: Summary Reports (`campusflow/reports.py`)
  - Unit tests for lifecycle, assignments, queue ordering, and reports (`tests/test_workflow.py`, `tests/test_reports.py`)
* **Shared / Integrated:**
  - F7: JSON Storage & Reload (`campusflow/storage.py`)
  - CLI Interface (`main.py`)
  - Common Exceptions (`campusflow/exceptions.py`)

---

## 2. Shared Data Structure: Ticket Schema

Each ticket is represented as a Python dictionary:
```python
{
    "id": "T001",              # Unique auto-incrementing ID: "T001", "T002", etc.
    "title": "Wi-Fi outage",   # Non-blank string
    "category": "Network",     # Normalized: "Network", "Hardware", "Software", "Other"
    "urgency": "high",         # Normalized: "low", "medium", "high"
    "affected_users": 15,      # Positive integer (> 0)
    "priority": "critical",    # Calculated: "critical", "high", "medium", "low"
    "status": "open",          # "open", "in_progress", "resolved"
    "assigned_to": None        # Non-empty string or None
}
```

The collection of tickets is maintained in-memory as a standard `list` of dictionaries (`tickets = [ticket1, ticket2, ...]`).

---

## 3. Error Handling Strategy

We adopt **Custom Domain Exceptions** (Option A).
All domain errors inherit from `CampusFlowError`:
* `CampusFlowError(Exception)`: Base exception.
* `ValidationError(CampusFlowError)`: Raised when input validation fails (e.g. empty title, non-positive integer, invalid category/urgency).
* `TicketNotFoundError(CampusFlowError)`: Raised when a requested ticket ID does not exist in the collection.
* `InvalidTransitionError(CampusFlowError)`: Raised when a status transition is invalid (e.g. unassigned ticket moved to `in_progress`, modifying resolved ticket without reopening).
* `StorageError(CampusFlowError)`: Raised when JSON data cannot be read, written, or is corrupted.

The CLI menu wraps user operations with `try...except CampusFlowError as e:` and prints user-friendly messages without crashing or corrupting data.

---

## 4. Module Responsibilities & Function Contracts

### 4.1 Exceptions (`campusflow/exceptions.py`)
Defines `CampusFlowError`, `ValidationError`, `TicketNotFoundError`, `InvalidTransitionError`, `StorageError`.

### 4.2 Ticket Creation & Priority (`campusflow/tickets.py`)
* `calculate_priority(urgency: str, affected_users: int) -> str`
  - Applies Priority Rules 1 through 4 in strict order.
* `validate_ticket_input(title: str, category: str, urgency: str, affected_users: Any) -> dict`
  - Validates and normalizes fields; raises `ValidationError` on bad input.
* `generate_next_id(tickets: list[dict]) -> str`
  - Determines the next sequential ID (e.g., `"T001"`, `"T002"`, ...) based on existing IDs in the collection, preventing ID collisions even after JSON reload.
* `create_ticket(tickets: list[dict], title: str, category: str, urgency: str, affected_users: Any) -> dict`
  - Validates input, generates next ID, creates ticket dictionary with default `status="open"`, `assigned_to=None`, appends to `tickets`, and returns the created ticket.
* `get_ticket(tickets: list[dict], ticket_id: str) -> dict`
  - Returns the ticket matching `ticket_id`, or raises `TicketNotFoundError`.
* `list_tickets(tickets: list[dict]) -> list[dict]`
  - Returns a copy/view of all tickets.

### 4.3 Workflow & Queue (`campusflow/workflow.py`)
* `assign_ticket(tickets: list[dict], ticket_id: str, staff_name: str) -> dict`
  - Assigns `ticket["assigned_to"] = staff_name.strip()`. Raises `TicketNotFoundError` if ID not found, `ValidationError` if `staff_name` is empty.
* `update_status(tickets: list[dict], ticket_id: str, new_status: str) -> dict`
  - Validates lifecycle transitions:
    - `open` -> `in_progress` (only allowed with a nonblank staff assignment).
    - `in_progress` -> `resolved`.
    - Any edit on `resolved` requires explicit `reopen_ticket`.
    - Raises `InvalidTransitionError` on illegal transition.
* `reopen_ticket(tickets: list[dict], ticket_id: str) -> dict`
  - Sets `status` back to `open` from `resolved`.
* `get_work_queue(tickets: list[dict]) -> list[dict]`
  - Implemented in `campusflow/reports.py`. Filters tickets where `status == "open"`.
  - This view shows tickets waiting to be started; `in_progress` and `resolved` tickets are excluded.
  - The future CLI should label this view "Open tickets awaiting work". Use list/view and status reports to inspect work already in progress.
  - This follows the guide's open-ticket queue acceptance scenario; Issue #2's broader "unresolved" wording needs alignment during partner review.
  - Sorts primarily by priority rank: `critical` (0) -> `high` (1) -> `medium` (2) -> `low` (3).
  - Ties are broken by earlier numeric ticket ID (e.g., `T001` before `T002`).

### 4.4 Reports (`campusflow/reports.py`)
* `generate_report(tickets: list[dict]) -> dict`
  - Returns total count, breakdown by status (`open`, `in_progress`, `resolved`), and breakdown by priority (`critical`, `high`, `medium`, `low`).
  - Gracefully handles empty ticket collections (zero tickets).

### 4.5 Persistence (`campusflow/storage.py`)
* `save_tickets(tickets: list[dict], filepath: str) -> None`
  - Atomically writes tickets to JSON file.
* `load_tickets(filepath: str) -> list[dict]`
  - Loads tickets from JSON file.
  - If file does not exist, returns empty list `[]` (fresh start).
  - If JSON is malformed/corrupted, raises `StorageError` with clear message without deleting the file.

### 4.6 Testing Isolation
All business functions accept pure data arguments (`tickets: list[dict]`, strings, ints) and return dicts or raise exceptions. No business logic functions invoke `input()` or `print()`. This allows fast, deterministic automated testing in `unittest`.

