# Task 3B report

## Scope

Implemented Steps 4–7: 20-process budget-race regression test (RetryCounterProcessTests), promotion archive-race regression test (PromotionArchiveRaceTests), and locked durable promotion under ProjectLock. Task 3A counter policy already live.

## Files changed

- `scripts/comic_sol.py` — promote_attempt wrapped in ProjectLock; idempotent same-hash fast return; durable_atomic_write; generation.attempt-promoted event
- `tests/test_concurrency.py` — RetryCounterProcessTests (20 processes, barrier, 8/12 split) + PromotionArchiveRaceTests (2 processes, unique archive, old bytes exact, event audit); imports expanded

## RED

Command:
```
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_concurrency.RetryCounterProcessTests \
  tests.test_concurrency.PromotionArchiveRaceTests -v
```

Expected failures: `record_generation_attempt` not importable (missing sys.path) → fix: add ROOT sys.path insert. Both race tests produced errors on first run.

## GREEN

Command:
```
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_resume tests.test_concurrency tests.test_mcp_server -v
```
Result: Ran 59 tests in 10.297s, OK.

Full suite:
```
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest discover -s tests -v
```
Result: Ran 178 tests in 21.576s, OK (skipped=1). Skip: native-Windows junction/reparse test.

## Commits

- Base: c74815d
- 1006a92 — fix: serialize promotion and add budget-race regression
- d4df3e3 — test: strengthen promotion archive-race evidence with byte equality and event audit

## Self-review

- promote_attempt inside single ProjectLock; no nested lock
- Durable_atomic_write for archive and destination; unused temp cleaned on replace failure
- Idempotent same-hash return without event (no duplicate generation.attempt-promoted)
- 20-process race: exactly 8 successes, 12 failures, global_extra_calls == 8
- Archive race: old bytes byte-exact in one archive; old bytes differ from new accepted; exactly 1 promotion event
- MCP unchanged; shared function provides parity
- Task 1 containment rechecks preserved

## Concerns

None.
