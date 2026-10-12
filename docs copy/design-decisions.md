# Proposed Team B integration contracts

These decisions are proposed for partner review, not recorded as a completed
agreement between fellows.

Use one shared list of dictionaries with the guide's eight required fields.
Team A owns creation, normalization, validation and priority calculation.
Team B owns `workflow.py`, `reports.py` and their tests. The integrated CLI and
storage module are shared responsibilities.

| Function | Result |
| --- | --- |
| `get_ticket(tickets, ticket_id)` | Existing ticket dictionary |
| `assign_ticket(tickets, ticket_id, staff_name)` | Updated ticket dictionary |
| `update_status(tickets, ticket_id, new_status)` | Updated ticket dictionary |
| `reopen_ticket(tickets, ticket_id)` | Updated ticket dictionary |
| `get_work_queue(tickets)` | New sorted list of existing ticket dictionaries |
| `generate_report(tickets)` | Dictionary with `total`, `by_status`, `by_priority` |

Workflow functions mutate the matching dictionary only after validating the
operation. Expected user errors raise `ValueError`; the CLI should catch it and
display the message. Business functions never prompt or print. Ticket IDs accept
case variations and surrounding whitespace; stored IDs are canonical `T001` etc.
Staff names are trimmed while preserving case. Status input is trimmed and
lowercased; canonical status is `in_progress`, with an underscore.

Only `open → in_progress → resolved` is allowed through `update_status`.
Starting work requires a nonblank assignment. Skipped, backward and same-status
transitions raise errors. Assignment and reassignment are allowed on open or
in-progress tickets. Resolved tickets reject assignment and status updates.
An explicit `reopen_ticket` sets a resolved ticket to open and retains its
assignment, allowing the next assignment or transition.

The queue includes **only status `open`**, following F5's wording and acceptance
scenario. In-progress and resolved tickets are excluded. Priority order is
critical, high, medium, low; ties use the integer portion of the ID so T010 sorts
before T1000. Sorting never changes the stored list. Returned queue dictionaries
are shared records: display them without editing their fields directly.

Reports count all tickets and always contain every canonical status and priority,
including zero counts. Creation and JSON loading must enforce valid schema,
unique canonical numeric IDs, and valid status/priority values before handing
records to these modules.

The future storage module should own JSON loading/saving. The CLI loads once at
startup and saves after each successful mutation. Missing files start an empty
collection; corrupt JSON must be reported without overwriting the original file.
Team A must generate IDs from the maximum existing numeric ID after loading.
All other editing functions must also respect the resolved-ticket lock.
