# CampusFlow — Technical Support Ticket Manager

CampusFlow is a Python command-line helpdesk ticket management system designed for campus technical support teams to record issues, automatically calculate priority, assign responsibility, track resolution workflows, and report metrics.

## Engineering Team
* **Engineer 1 (wib3):** Ticket Creation, Validation, Priority Engine, Ticket View (`campusflow/tickets.py`), and Unit Tests (`tests/test_tickets.py`).
* **Engineer 2 (rolandelaigwu6-ui):** Ticket Assignment, Lifecycle Workflow, Work Queue, Reporting (`campusflow/workflow.py`, `campusflow/reports.py`), and Unit Tests (`tests/test_workflow.py`).

## Core Features
1. **F1 — Ticket Creation & Validation:** Validates title, category, urgency, and positive user count. Automatically generates unique IDs (`T001`, `T002`, ...).
2. **F2 — List / View:** Displays all tickets and inspects ticket details.
3. **F3 — Assignment:** Assigns tickets to staff members; validates IDs and non-empty names.
4. **F4 — Lifecycle Workflow:** Enforces valid transitions (`open` -> `in_progress` -> `resolved`), requires assignment before progress, and explicit reopen for resolved tickets.
5. **F5 — Work Queue:** Lists unresolved tickets ordered by priority (`critical` -> `high` -> `medium` -> `low`) and breaks ties by ticket ID.
6. **F6 — Reports:** Summarizes total tickets with breakdowns by status and priority.
7. **F7 — Persistence:** Safe JSON save/load with support for fresh start on missing file and error detection on malformed data.

## Running CampusFlow
```bash
python3 main.py
```

## Running Automated Tests
```bash
python3 -m unittest discover -s tests -v
```

## Documentation
* [Architecture & Design Decisions](docs/design-decisions.md)
* [AI Learning Log](docs/ai-learning-log.md)