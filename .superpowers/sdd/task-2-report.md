# Integrity Core Task 2 Report

Status: DONE

## Files

- `scripts/project_io.py`: added stdlib cross-platform `ProjectLock`, `fsync_directory`, and `durable_atomic_write`.
- `scripts/comic_sol.py`: retained `atomic_write_bytes` as compatibility wrapper over durable writer.
- `scripts/export_pdf.py`: final verified PDF publication now uses durable writer.
- `tests/test_concurrency.py`: real-subprocess exclusion, release, and retained sanitized metadata coverage.
- `tests/test_project_io.py`: syscall ordering and replace-failure atomicity coverage.
- `tests/test_export_pdf.py`: final PDF durable-writer adoption coverage.

## RED evidence

Lock command:

```text
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest tests.test_concurrency.ProjectLockTests -v
Ran 3 tests in 0.005s
FAILED (errors=3)
AttributeError: module 'scripts.project_io' has no attribute 'ProjectLock'
```

Durability command:

```text
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest tests.test_project_io.DurableWriteTests -v
Ran 2 tests in 0.004s
FAILED (errors=2)
AttributeError: module 'scripts.project_io' has no attribute 'durable_atomic_write'
```

Tests existed and failed before matching production code. Lock contention uses child Python processes, not threads.

## GREEN evidence

```text
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest tests.test_project_io.DurableWriteTests -v
Ran 2 tests in 0.002s
OK
```

```text
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest tests.test_project_io tests.test_concurrency tests.test_export_pdf -v
Ran 20 tests in 2.897s
OK (skipped=1)
```

Skip: native-Windows junction/reparse behavior under WSL; pre-existing Task 1 platform skip.

## Full suite

```text
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest discover -s tests -v
Ran 168 tests in 19.510s
OK (skipped=1)
```

`git diff --check` passed before commit. `python -m compileall -q scripts tests` passed.

## Commit

Implementation commit: `aedf4a1e141fbf28e216cfd5eb77bf3d0c9ffae3` (`fix: lock projects and durably publish artifacts`).

## Self-review

- Scope limited to exact Task 2 production/test files; schema v1 and Task 1 containment untouched.
- POSIX uses `fcntl.flock`; Windows uses one initialized byte with `msvcrt.locking`.
- Retry loop handles lock-contention errno/winerror values; unrelated errors propagate.
- Lock metadata contains ASCII PID plus newline only; unlock and close run in `finally`; lock file remains.
- Durable ordering asserted as write, flush, file fsync, replace, directory fsync.
- Replace failure preserves destination and removes owned temporary file.
- Directory fsync no-op exists only on Windows because stdlib cannot fsync directories there; POSIX errors propagate.
- Final PDF stays staged and verified before durable publication.

## Concerns

- Native Windows lock path not executed under WSL. Logic follows required `msvcrt` one-byte contract; dedicated native-Windows validation remains advisable.
