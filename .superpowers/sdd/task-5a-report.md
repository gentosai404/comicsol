# Task 5A report

## Scope

Implemented Steps 1–3 of `.superpowers/sdd/task-5-brief.md`: fail-closed final and export-ready artifact validation, page-QA schema, `require_valid_project`.

## RED-GREEN evidence

### RED

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest tests.test_finalization.FinalArtifactTests -v
```

Initial failures:
- `test_final_fails_without_any_artifacts`: `artifacts={}` returned no issues from `validate_project(project, "final")`.
- `test_export_ready_excludes_report_and_pdf`: `ValueError: unknown validation stage: export-ready`.
- `test_export_ready_reports_missing_page_qa`: same stage error.

### GREEN

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest tests.test_finalization -v
# 5 PASS

/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_finalization tests.test_validation tests.test_export_pdf tests.test_manifest -v
# 69 PASS

/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest discover -s tests -v
# 190 PASS, 1 native-Windows skip
```

## Implementation

### `scripts/validate_project.py`

- Added `export-ready` to `STAGES`.
- `validate_page_qa_record`: exact schema `{page, page_path, page_sha256, schema_version, status}`; `status == "reviewed"`; page/path agreement with canonical numbering; SHA-256 hash binding.
- `require_valid_project(project_dir, stage)`: raises `ProjectValidationError` when issues exist.
- Fail-closed artifact enumeration for `final` and `export-ready`:
  - Required descriptors: `character_bible`, `story_plan`, `storyboard`, `composition_cache` (always); `qa_report`, `pdf` (final only).
  - Canonical path enforcement for each descriptor.
  - Page-QA records per page count with hash binding.
  - Lettered panels per manifest panel list.
  - Composed page PNGs per page count.
  - Composition cache file existence.
  - Report and PDF existence (final only).
- `composition_cache` added to allowed manifest artifact names.

### `templates/page-qa.json`

Canonical schema template per brief.

### `tests/test_finalization.py`

- `FinalArtifactTests`: empty artifacts fail final; export-ready passes with complete panel/page-QA/composition-cache set; missing page-QA reported.
- `GuardedOperationTests`: `require_valid_project` raises on invalid, returns None on valid.

### Existing test adaptation

- `test_final_stage_requires_panel_warnings_and_warning_terminal`: changed from `assertEqual([], ...)` to asserting no `status`/`warnings` issues, because fail-closed final now correctly reports missing artifacts in a fixture that only has panel files.
- `test_mcp_server`: changed `comic_validate` stage from `final` to `panels` because the sample fixture lacks final artifacts.

## Commits

- `8094e87` — `fix: add fail-closed final/export-ready artifact enumeration and page-QA validation`

## Self-review

- Fail-closed: empty `artifacts={}` now produces issues at final stage.
- export-ready excludes report/PDF/export cache as specified.
- Page-QA hash binding verified against actual page PNG.
- Canonical path enforcement prevents descriptor path spoofing.
- `require_valid_project` interface matches brief exactly.
- No nested lock introduced; no Task 7 integration.
- Native Windows junction behavior remains honest Cannot verify under WSL.
