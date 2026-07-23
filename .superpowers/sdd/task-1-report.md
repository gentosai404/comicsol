# Integrity Core Task 1 Report

## Status

DONE

## Implementation commit

`ca2e58238c5267278a70592031b090cceb240f39` — `fix: enforce shared source and project boundaries`

## Files changed

- `scripts/project_io.py` — shared source-byte validator and contained project-path resolver.
- `scripts/comic_sol.py` — validate source before allocation; route project-controlled mutation paths through shared resolver.
- `scripts/mcp_server.py` — preserve relative path trust boundary for attempt record/promotion calls.
- `scripts/validate_project.py` — replace local resolver and re-check JSON/raster containment immediately before reads.
- `scripts/compose_pages.py` — reject absolute/external/symlink artifact paths and re-check before image reads.
- `scripts/letter_panels.py` — resolve/re-check project-controlled JSON and image paths.
- `tests/test_project_io.py` — lexical, sibling-prefix, symlink, and valid containment coverage.
- `tests/test_manifest.py` — oversized, invalid UTF-8, `.pdf`, and `.json` source-boundary coverage.
- `tests/test_composition.py` — absolute and symlink artifact rejection coverage.
- `tests/test_mcp_server.py` — oversized MCP payload rejection before allocation.

## RED evidence

### Source boundary

Command:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_manifest.SourceBoundaryTests -v
```

Result: expected RED, exit 1. 3 tests ran with 4 failures:

- `.pdf` CLI source returned `0`, expected `1`.
- `.json` CLI source returned `0`, expected `1`.
- invalid UTF-8 raised no `ValueError`.
- 200 KiB + 1 source raised no `ValueError`.

### Path containment

Command:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_project_io tests.test_composition -v
```

Result: expected RED, exit 1. 10 tests ran with 2 failures and 1 error:

- `contained_project_path` import failed because interface did not exist.
- absolute manifest panel path raised no `ValueError`.
- symlink manifest panel path raised no `ValueError`.

## GREEN evidence

### Source boundary

Command:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_manifest.SourceBoundaryTests \
  tests.test_mcp_server.McpServerUnitTests.test_init_rejects_oversized_utf8_before_project_allocation -v
```

Result: 4 tests passed.

### Path containment

Command:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_project_io tests.test_composition -v
```

Result: 13 tests passed.

### Focused suite

Command:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_project_io tests.test_manifest tests.test_composition \
  tests.test_validation tests.test_mcp_server -v
```

Initial result: 74 passed, 1 error. Shared resolver correctly rejected an MCP-generated absolute in-project path created by the adapter. Adapter fixed to preserve caller-provided relative paths. Rerun result: 75 tests passed.

### Full suite

Command:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest discover -s tests -v
```

Initial result: 151 passed, 2 errors. Existing direct Python callers supplied absolute in-project attempt paths. Compatibility wrapper now converts only absolute paths already contained by project root into relative paths before shared resolution; external absolute paths remain rejected.

Fresh final result: 153 tests passed in 19.088s; 0 failures, 0 errors.

## Self-review

- Requirements checked against `task-1-brief.md`; work limited to Task 1 trust boundaries.
- Source validation executes before `_allocate_project_directory()`.
- CLI suffix validation uses exact `.txt`/`.md` allowlist; MCP passes text bytes through suffix-neutral core validation.
- Resolver rejects empty, POSIX absolute, Windows drive, traversal, sibling-prefix escape, and symlink paths.
- Composition no longer supports absolute artifact paths.
- Validation and lettering re-check containment immediately before project-controlled reads.
- Existing direct API compatibility retained only for absolute paths proven already inside project root; shared public resolver remains relative-only.
- `git diff --check` passed before commit.
- No new dependency added.

## Whitespace gate fix

Command:

```bash
git diff --check 1f0592f..HEAD
```

Exact result: no output; exit code `0`.

Command:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest tests.test_project_io -v
```

Exact result:

```text
test_rejects_absolute_traversal_and_windows_drive_paths (tests.test_project_io.ContainedProjectPathTests.test_rejects_absolute_traversal_and_windows_drive_paths) ... ok
test_rejects_sibling_prefix_escape (tests.test_project_io.ContainedProjectPathTests.test_rejects_sibling_prefix_escape) ... ok
test_rejects_symlink_to_external_file (tests.test_project_io.ContainedProjectPathTests.test_rejects_symlink_to_external_file) ... ok
test_returns_resolved_contained_path (tests.test_project_io.ContainedProjectPathTests.test_returns_resolved_contained_path) ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.001s

OK
```

Exit code: `0`.

## Concerns

None.
