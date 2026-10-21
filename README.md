# CampusFlow — Technical Support Ticket Manager

CampusFlow is a Python command-line helpdesk ticket management system designed for campus technical support teams to record issues, automatically calculate priority, assign responsibility, track resolution workflows, and report metrics.

## Original CampusFlow Team
* **Engineer 1 (wib3):** Ticket Creation, Validation, Priority Engine, Ticket View (`campusflow/tickets.py`), and Unit Tests (`tests/test_tickets.py`).
* **Engineer 2 (rolandelaigwu6-ui):** Ticket Assignment, Lifecycle Workflow, Work Queue, Reporting (`campusflow/workflow.py`, `campusflow/reports.py`), and Unit Tests (`tests/test_workflow.py`).

## CampusFlow Next responsibilities

Engineer A owns validation, lifecycle safety, note business rules, and storage.
Engineer B owns search, reports, note CLI interaction, and the understanding check.
The current Engineer A working branch is `integration/teamA-test`.
Both engineers must provide their full names and actual PR/review links before submission.

## Core Features
1. **F1 — Ticket Creation & Validation:** Validates title, category, urgency, and positive user count. Automatically generates unique IDs (`T001`, `T002`, ...).
2. **F2 — List / View:** Displays all tickets and inspects ticket details.
3. **F3 — Assignment:** Assigns tickets to staff members; validates IDs and non-empty names.
4. **F4 — Lifecycle Workflow:** Enforces valid transitions (`open` -> `in_progress` -> `resolved`), requires assignment before progress, and explicit reopen for resolved tickets.
5. **F5 — Work Queue:** Lists only open tickets awaiting work (excluding in_progress and resolved), ordered by priority (`critical` -> `high` -> `medium` -> `low`) and breaks ties by ticket ID.
6. **F6 — Reports:** Summarizes total tickets with breakdowns by status and priority.
7. **F7 — Persistence:** Safe JSON save/load with support for fresh start on missing file and error detection on malformed data.

## CampusFlow Next Features (Sprint 2)
8. **Requirement A — Centralized Validation & Lifecycle Safety:** Type-pure validation (`affected_users` positive integers, non-blank title, legal category/urgency). Unassigned tickets cannot enter `in_progress`. Resolved tickets cannot be mutated without explicit reopen. All rejected operations guarantee zero mutation of stored tickets.
9. **Requirement B — Structured Follow-up Notes:** Threaded notes per ticket (`note_id`, `author`, `message`). Sequential IDs (`N001`, `N002`, ...); rejected notes do not consume IDs. Notes allowed only on `open` or `in_progress` tickets.
10. **Requirement E — Safe JSON Persistence & Validation:** Atomic JSON save/load with full collection schema validation on load. Corrupted files, duplicate ticket IDs, tampered priority, or schema violations raise `StorageError` and preserve in-memory state. Backward-compatible migration ensures legacy tickets without notes are seamlessly upgraded.

11. **Search:** Case-insensitive title substring matching with category, status, and priority filters combined using AND.
12. **Reports:** Status, priority, and category counts, resolved/unresolved totals, and resolution percentage (0% for no tickets).
13. **Understanding Check:** Six multiple-choice questions, invalid-answer retries, a score out of six, and two explanations displayed for discussion.

## Domain inputs and storage compatibility

`create_ticket(tickets, title, category, urgency, affected_users)` requires an actual
positive integer for `affected_users`; strings, booleans, and floats are rejected.
The CLI converts keyboard input before calling this API. Validation errors use
`CampusFlowError` subclasses and leave the collection unchanged.

The JSON array format is unchanged. Loading legacy tickets with no `notes` key
adds an empty list in memory without rewriting the source file. Explicit `null`
or malformed notes are rejected. All other schema fields remain required.
Stored IDs require uppercase `T`/`N` and a positive ASCII numeric suffix;
existing padding is retained, and generated IDs use at least three digits.
Malformed records, invalid UTF-8, and duplicates reject the whole load. Back up
and correct rejected files; loading never silently renames or drops records.

## JSON Storage Envelope Format
Tickets are persisted as a JSON array of ticket objects (`data/tickets.json`):
```json
[
  {
    "id": "T001",
    "title": "Wi-Fi outage in CS lab",
    "category": "Network",
    "urgency": "high",
    "affected_users": 15,
    "priority": "critical",
    "status": "in_progress",
    "assigned_to": "Ada",
    "notes": [
      {
        "note_id": "N001",
        "author": "Ada",
        "message": "Power-cycled access point AP-04."
      }
    ]
  }
]
```

## Running CampusFlow
```bash
python3 main.py
```

## Running Automated Tests
```bash
python3 -m unittest discover -s tests -v
```

## Documentation
* [Diagnostic Baseline Check](docs/baseline-check.md)
* [Architecture & Design Decisions](docs/design-decisions.md)
* [AI Learning Log & Defense Questions](docs/ai-learning-log.md)

## Integration Status
* **F1 — Ticket Creation & Validation:** (`campusflow/tickets.py`)
* **F2 — List & View Tickets:** (`campusflow/tickets.py`)
* **F3 — Staff Assignment:** (`campusflow/workflow.py`)
* **F4 — Lifecycle Transitions & Reopen:** (`campusflow/workflow.py`)
* **F5 — Open-Ticket Work Queue:** (`campusflow/reports.py`)
* **F6 — Summary Reports:** (`campusflow/reports.py`)
* **F7 / Req E — Safe JSON Persistence & Full Collection Validation:** (`campusflow/storage.py`)
* **Req A — Centralized Validation Helpers & Invariants:** (`campusflow/validation.py`)
* **Req B — Structured Follow-up Notes:** (`campusflow/notes.py`)
* **Interactive CLI Interface:** (`main.py`)

See [Engineer A verification and integration notes](docs/engineer-a-verification.md) for this reliability change and remaining review evidence.

Empty saves are supported for new projects and files already containing `[]`.
Because CampusFlow has no delete-all operation, saving an empty collection over
an existing populated file raises `StorageError` and preserves the original file.
An empty save also preserves existing malformed or unreadable files.

## Ticket data on another computer or in Codespaces

The application uses `data/tickets.json` beside `main.py`, regardless of the
terminal's working directory. Startup displays its absolute location and creates
an empty JSON file for a fresh project. Viewing tickets reads the collection
loaded at startup; successful ticket changes save it immediately.

Git ignores `data/`, so cloning code or opening a new Codespace does not copy
another installation's tickets. To continue the same dataset, stop the app in
both places, back up any destination file, and copy the source `data/tickets.json`
into the destination project's `data/` folder. In Codespaces, create/expand that
folder and upload the file using Explorer. Restart the application to load it.
Do not overwrite a different dataset without retaining a backup. This CLI uses
local JSON storage and does not synchronize records between computers.

## Review saved demonstration tickets in a fresh clone

[examples/demo-tickets.json](examples/demo-tickets.json) is a versioned JSON
example containing four dummy tickets across open, in-progress, and resolved
states, with assignments and follow-up notes. It can be inspected directly on
GitHub without running the application.

In a fresh clone or Codespace, **before starting the application**, run:

```bash
python prepare_demo.py
python main.py
```

Choose **View All Tickets**, then view individual tickets or their notes. Changes
are saved to the local `data/tickets.json` and are available after restarting.
New ticket IDs continue at `T005`; T001's next note ID is `N002`.

The preparation command refuses to replace any existing `data/tickets.json`,
including an empty file. If you already started the app, stop it and retain a
backup of that file before moving it aside and preparing the demo. The tracked
example is never changed by this command. To review actual records elsewhere,
transfer your saved local JSON as described above; demo records are not your
live dataset. The example and preparation script become available in fresh
clones once committed, pushed, and included in the branch being cloned.
