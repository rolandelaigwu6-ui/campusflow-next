# Engineer A reliability verification — 2026-10-16

Branch: `integration/teamA-test`. Starting commit: `45c263a`.
Changes and checks in this record were performed with AI assistance. This record
is not a substitute for either engineer's independent learning or peer review.

## Reproduced failures before editing

- `create_ticket(..., affected_users="10")` accepted a string.
- Loading `notes: null` succeeded; displaying the ticket then raised `TypeError`.
- Loading a list-valued status or priority raised uncaught `TypeError`.
- `T001` and `t001` loaded together, despite normalized lookup.
- `T²` and `N²` loaded, then numeric ID generation raised `ValueError`.

The existing 92 tests passed despite these failures. Tests of a strict helper
alone did not establish that ticket creation actually used that helper.

## Changes and regression evidence

Creation and workflow use centralized validators. The CLI converts the count to
an integer and wraps invalid conversions in `ValidationError`. Storage validates
notes and IDs, rejects invalid enum types safely, and wraps UTF-8 decoding errors.
The JSON list format, priority calculation, queue, and lifecycle are preserved.
Existing legacy tickets lacking notes still migrate on successful load.

`tests/test_reliability_regressions.py` exercises public APIs for rejected creation,
whole-batch rejection, source-file preservation, malformed notes, duplicate note
IDs, UTF-8 failure, CLI conversion, and report behavior through resolve/reopen.
An original normalization test now supplies integer 15 instead of string "15",
reflecting the explicit Next contract; a new test verifies string rejection.

## Cross-module bug-hunter candidate for Engineer A

This is an AI-assisted candidate for the engineer to predict, run, and explain,
not evidence of an independently devised personal exercise.

- Initial state: one open ticket with two follow-up notes.
- Input: assign, start, resolve, generate report, reopen, generate report again.
- Expected: initially 100% resolved; after reopen, total 1, open 1,
  unresolved 1, resolved 0, resolution 0%; notes never increase ticket counts.
- Actual: passed; the existing report implementation needed no correction.
- Test: `test_report_tracks_reopen_and_counts_ticket_once_despite_notes`.
- Code change: regression coverage only; no Engineer B report logic changed.

## Integration notes for Engineer B

- Public function signatures, return values, and exception types are unchanged.
- Intentional contract correction: direct creation calls must pass integer counts.
- `main.py` changes only the import and count conversion in `handle_create_ticket`.
  Retain that conversion if another branch edits the same handler.
- Search, report, quiz, and note CLI implementations are untouched.
- Compare Engineer B's latest branch before opening/merging the PR and rerun
  `python -m unittest discover -s tests -v` on the integrated result.

## Evidence still requiring the engineers

- Confirm both current full names and provide actual feature PR/issue URLs.
- Run and explain the new regressions independently; do not claim AI-written
  tests as independently authored work.
- Complete two genuine learning cycles each, including unrelated experiments.
  The existing AI log has inconsistent note-counter accounts (Interaction #5
  versus defence answer #7); reconcile these from the real conversation evidence.
  No historical AI advice or personal reflection was invented by this update.
- Complete reciprocal reviews with at least two specific observations each,
  relevant test execution, addressed blocking feedback, and approval before merge.
- Engineer B still owns the separate sorted-search view and their learning notes.
- Supply individual reflections, quiz demonstration, final merged SHA, and
  fresh-clone test output. These have not been claimed complete here.


## PR #4 review follow-up — empty-save protection

Reviewer `maihwe` identified a potential overwrite risk: an unexpectedly empty
in-memory collection could replace an existing populated file with `[]`.
The regression `test_empty_save_preserves_populated_file` was run before the fix
and failed with `AssertionError: StorageError not raised`.

`save_tickets` now checks existing storage before an empty save. It permits new
files and valid empty datasets, rejects populated datasets with `StorageError`,
and propagates storage validation/read errors without replacing their files.
This policy fits the current CLI, which has no ticket deletion/reset operation.
The function signature and JSON format are unchanged. It is not a concurrent
multi-process locking mechanism; the application remains a local CLI.

Three new tests cover populated-file preservation, fresh/empty project saves,
and malformed source-file preservation. The integrated suite passes 106 tests.
This is recorded review-driven implementation evidence, not a claim of approval.

## Fresh-clone storage visibility follow-up

A Codespaces screenshot showed no tickets on a separate main-branch checkout.
Local runtime data is excluded by Git, so no local tickets are transferred by
cloning. Previously, merely launching and viewing an empty project did not create
a JSON file. Startup now initializes missing storage to `[]`, prints its location,
and anchors the default path to the project rather than the working directory.
Existing files are loaded without replacement; invalid files still stop startup.
Three startup regressions cover initialization, reload, and corrupt-file protection.
The integrated suite passes 109 tests. Cross-machine transfer remains an explicit
file copy; no shared database or synchronization service was introduced.
