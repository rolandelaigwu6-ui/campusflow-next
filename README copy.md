# CampusFlow — Team B contribution

Python standard-library implementation of Engineer B's assignment, lifecycle,
open-ticket queue, and reports from the sprint guide.

Run from this directory with Python 3.8 or newer:

```sh
python3 -m unittest discover -s tests -v
python3 demo_team_b.py
```

The demo uses sample tickets in memory and demonstrates priority ordering,
an invalid unassigned transition, assignment, resolution, reporting, the
resolved-ticket lock, and explicit reopening.

- `campusflow/workflow.py`: lookup, assignment, status advancement, reopening.
- `campusflow/reports.py`: open-ticket queue and status/priority counts.
- `tests/`: success, invalid input, numeric sorting, zero counts, and mutation tests.
- `docs/design-decisions.md`: proposed integration contracts for Team A.
- `docs/team-b-review.md`: acceptance mapping and human review checklist.

This is the Team B component, not the complete seven-feature application.
Team A's creation/validation/priority engine, the shared interactive CLI and JSON
persistence still need integration. No third-party packages are required.
The modules assume valid ticket records from creation or validated JSON loading.
The collection is in memory; these functions do not save it themselves.

No Git repository or GitHub reviews are present in this workspace. Fellow names,
issue numbers, branch/PR links, partner approval and personal learning evidence
must be supplied through the actual team process before submission.
