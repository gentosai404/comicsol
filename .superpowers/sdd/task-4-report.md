# Task 4 report

## Scope

Implemented `ProjectTransaction`, all-or-nothing page composition, and crash recovery per `.superpowers/sdd/task-4-brief.md`.

## RED-GREEN evidence

### Mixed-page regression

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_composition.CompositionTests.test_failed_second_page_preserves_entire_prior_page_set -v
```

RED baseline: prior `compose_all_pages()` published pages one-by-one, allowing page 1 replacement before page 2 decode failed.

GREEN: all pages now resolve, decode, and render before `ProjectTransaction` starts publication. Corrupt page 2 raises `ValueError`; both old page hashes remain unchanged; no staging files remain.

### Transaction rollback and recovery

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_project_io.ProjectTransactionTests -v
```

- `test_second_publish_failure_restores_prior_set`: injected `OSError` on second staged replace; old bytes restored.
- `test_recover_restores_interrupted_publishing_transaction`: simulated `KeyboardInterrupt` after first replace; `recover()` restored old set.
- `test_rollback_removes_newly_created_targets_without_backup`: injected second-publish failure on first-ever composition; newly visible page is removed.
- `test_recover_removes_newly_created_targets_after_interrupted_first_composition`: interrupted first composition leaves no partial page set after recovery.
- `test_stage_bytes_rejects_traversal`: rejects `../`, nested traversal, drive-relative, and UNC paths.
- `test_recover_rejects_malicious_journal_paths`: malicious journal cannot escape project root.

## Failed review and repair

Initial independent review found two Important defects:

1. rollback did not remove newly-created targets where `backup` was null;
2. transaction and recovery paths were not all validated through shared containment.

Both were reproduced as RED failures, fixed in `91dd643`, and covered by regression tests above.

## Implementation

### `scripts/project_io.py`

- `ProjectTransaction.__enter__`: acquires one `ProjectLock`, creates numbered `logs/transactions/<id>/`.
- `stage_bytes`: saves durable indexed backup and staged payload under transaction directory.
- `commit`: writes canonical durable journal in `publishing` phase before first destination replace; publishes staged files; rolls back reverse-order on failure.
- `recover`: acquires one `ProjectLock`, rolls back every non-committed journal, cleans transaction directories.
- cleanup: removes committed/rolled-back directory and fsyncs parent.

### `scripts/compose_pages.py`

`compose_all_pages()` resolves and decodes all sources and renders every payload before opening one `ProjectTransaction`. Publication uses `stage_bytes()` and one `commit()`.

## Verification

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_project_io tests.test_composition -v
# 22 PASS, 1 native-Windows skip

/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest discover -s tests -v
# 185 PASS, 1 native-Windows skip

git diff --check
# exit 0
```

## Commits

- `1641f01` — `fix: publish composed page sets transactionally using ProjectTransaction`
- `b863e2c` — `fix: hold ProjectLock in recover and fsync after cleanup`
- `91dd643` — `fix: reject traversal and remove new targets on rollback`

## Self-review

- Exact required interfaces present.
- One lock per transaction/recovery; no nested lock.
- Project-local staged files, backups, journal.
- Journal project-relative paths.
- Journal durable before first replacement.
- Reverse-order rollback on caught failure.
- Recovery restores interrupted publication.
- All pages pre-rendered before any visible replacement.
- No Task 7 mutation integration.
- Native Windows junction behavior remains honest Cannot verify under WSL.
