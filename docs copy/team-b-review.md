# Team B review handoff

## Acceptance mapping

| Requirement | Implementation | Evidence |
| --- | --- | --- |
| F3 assignment and unknown ID rejection | `assign_ticket`, `get_ticket` | Assignment, blank name, invalid/unknown ID tests |
| F4 lifecycle and explicit reopening | `update_status`, `reopen_ticket` | Full lifecycle, assignment guard, invalid transitions, resolved lock tests |
| F5 open queue with numeric tie-break | `get_work_queue` | All four priorities, T002/T010/T1000, status filtering, unchanged storage |
| F6 totals and breakdowns | `generate_report` | Empty report and mixed status/priority counts |

## Human review checklist

- Run `python3 -m unittest discover -s tests -v` and inspect the actual output.
- Run `python3 demo_team_b.py` and explain why the two rejected operations fail.
- Check that rejected workflow operations preserve every ticket field.
- Confirm the open-only queue interpretation and assignment retention on reopen.
- Agree on function names and return contracts with Team A before CLI integration.
- Review JSON persistence and creation after integration; they are outside this slice.

## Suggested PR description

Implement ticket assignment, guarded status transitions and explicit reopening,
plus an open-ticket queue sorted by priority and numeric ID and reports with
zero-filled status/priority counts. Add 18 unittest cases and an in-memory demo.

Validation: `python3 -m unittest discover -s tests -v` and
`python3 demo_team_b.py`. Attach your actual output when opening the PR.
Add the real related issue and request your partner's review. This file records
no human review observations, approval or merge.

## Learning prompts for your own verified log

Use these to study the implementation and run your own experiments. These are
not completed personal learning entries:

1. Why must validation happen before mutating a shared dictionary? Predict and
   run an invalid transition; compare the ticket before and after.
2. How does tuple sorting implement priority and numeric ID tie-breaking?
   Predict the order of T010 and T1000, then compare string and integer sorting.
3. Why would including every unresolved ticket differ from the guide's open
   queue acceptance scenario? Examine the filtering test and explain your choice.

Record your real initial understanding, prompt, prediction, observed result and
decision in the guide's learning-log template. Include a suggestion you actually
corrected, improved or rejected; do not invent learning or partner review evidence.
