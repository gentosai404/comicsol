# Task 3A report

## Scope

Implemented Steps 1–3 only: strict generation-attempt policy, raster validation, locked durable counters, sanitized success event. No 20-process test, promotion change, Task 4 journal, or MCP change.

## RED

Command:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_resume.ResumeTests.test_second_initial_is_rejected_without_mutation \
  tests.test_resume.ResumeTests.test_second_transient_repeat_is_rejected_without_mutation \
  tests.test_resume.ResumeTests.test_third_visual_retry_is_rejected_without_mutation \
  tests.test_resume.ResumeTests.test_corrupt_raster_is_rejected_without_mutation \
  tests.test_resume.ResumeTests.test_small_raster_is_rejected_without_mutation \
  tests.test_resume.ResumeTests.test_ninth_global_extra_is_rejected_and_initials_are_excluded \
  tests.test_resume.ResumeTests.test_successful_attempt_appends_sanitized_event -v
```

Exit: `1`. Exact failures:

- `test_second_initial_is_rejected_without_mutation`: `AssertionError: ValueError not raised`
- `test_second_transient_repeat_is_rejected_without_mutation`: `AssertionError: ValueError not raised`
- `test_corrupt_raster_is_rejected_without_mutation`: `AssertionError: ValueError not raised`
- `test_small_raster_is_rejected_without_mutation (size=(511, 512))`: `AssertionError: ValueError not raised`
- `test_small_raster_is_rejected_without_mutation (size=(512, 511))`: `AssertionError: ValueError not raised`
- `test_successful_attempt_appends_sanitized_event`: `AssertionError: 'generation.attempt-recorded' != 'project.created'`

Existing third-visual and ninth-global checks passed RED. Expanded assertions still prove mutation-free rejection and global semantics while new failures exposed missing policy/raster/event behavior.

## GREEN

Focused policy command above: `Ran 7 tests in 0.403s`, `OK`.

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest tests.test_resume -v
```

Result: `Ran 44 tests in 1.550s`, `OK`.

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_resume tests.test_concurrency tests.test_mcp_server -v
```

Result: `Ran 57 tests in 9.055s`, `OK`.

## Full suite

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest discover -s tests -v
```

Result: `Ran 176 tests in 19.689s`, `OK (skipped=1)`. Skip: native-Windows junction/reparse test.

## Commits

- Base: `33961016a7980f8ce2422fe70237e1238935bdf0`
- Interim implementation: `dfca8ad6280ed31d1a865eda1ea4d186def65533` (`fix: enforce locked generation attempt budgets`)
- Report: recorded by following commit.

## Self-review

- One `ProjectLock`; no nested lock.
- Immediate contained-path recheck under lock with `must_exist=True`.
- Raster decoded and minimum width/height verified before counter read or mutation.
- Exact per-panel limits: initial 1, transient repeat 1, visual retry 2.
- Global extra limit 8; initial excluded, transient and visual included.
- Counter publication uses existing durable atomic JSON path.
- Sanitized `generation.attempt-recorded` append occurs after counter write while lock held.
- Rejection tests compare exact counter and event bytes, including missing counter-file state.
- Return keys and schema version preserved.
- MCP unchanged; shared function already supplies parity.

## Concerns

None in bounded Task 3A. Counter write intentionally precedes event append per brief; event I/O failure can leave durable counter without matching event and is outside rejected-call policy.
