# Comic Sol Lab v2 Integrity Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers/subagent-driven-development (recommended) or superpowers/executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the 13 audited Integrity Core defects so Comic Sol fails closed, recovers safely, enforces retry budgets across processes, completes the deterministic lifecycle through CLI/MCP, and continuously verifies advertised source-level platforms.

**Architecture:** Keep the current scripts-first codebase and extract only one shared reliability module for containment, locking, durable writes, and project transactions. Existing CLI and MCP functions continue as thin callers into deterministic engine functions. Every defect is fixed through a focused RED-GREEN cycle before any packaging, provider, installer, or broad comic-quality work begins.

**Tech Stack:** Python 3.11 stdlib, Pillow 11.3.0, MCP SDK 1.28.1, `unittest`, GitHub Actions.

## Global Constraints

- Work only in private repository `wenn-id/comic-sol-lab` on an `ai/*` branch.
- Do not modify or push `wenn-id/comic-sol/main`.
- Preserve existing schema-v1 projects unless a migration is explicit and tested.
- Use stdlib before new dependencies; add no runtime dependency for locking or transactions.
- Use strict TDD: each production behavior must first have a test that fails for the intended reason.
- Keep CLI, MCP, composition, validation, and lifecycle rules backed by the same engine functions.
- Sampling remains disabled in MCP.
- Reject arbitrary filesystem access and arbitrary command execution.
- Source input is UTF-8 `.txt` or `.md`, maximum 200 KiB measured as UTF-8 bytes.
- Per panel: one initial attempt, one transient repeat, two visual retries; project maximum eight extra calls.
- A terminal project requires current deterministic artifacts; missing descriptors never imply success.
- Base tests must pass without MCP installed; MCP tests run only in the MCP-extra environment.
- Support Linux, macOS, Windows native, WSL, and containers at source level.
- Do not begin installer, provider, GUI, or broad Comic Quality milestone work in this plan.

---

## File Map

### New files

- `scripts/project_io.py` — shared source validation, project containment, cross-process lock, durable atomic writes, and rollback-capable project transaction.
- `tests/test_project_io.py` — focused boundary, lock, durability, and transaction tests.
- `tests/test_concurrency.py` — real subprocess tests for retry counters and promotion archives.
- `tests/test_finalization.py` — fail-closed final validation, guarded export/transition, report/finalize, and complete MCP lifecycle tests.

### Modified files

- `scripts/comic_sol.py` — consume shared I/O primitives; source boundary; lock mutations; retry policy; recoverable `BLOCKED`; guarded terminal transition; resumable deterministic lifecycle.
- `scripts/validate_project.py` — use shared containment and require final artifact descriptors/files/hashes.
- `scripts/compose_pages.py` — contained inputs, pre-render all pages, transactionally publish page set.
- `scripts/letter_panels.py` — use shared contained paths where project-controlled paths are read.
- `scripts/export_pdf.py` — durable publication and engine-guarded export preconditions.
- `scripts/render_report.py` — expose a callable `render_report(project_dir)` engine boundary around the existing report renderer.
- `scripts/mcp_server.py` — expose resume, report, and finalize; route all lifecycle calls through engine functions.
- `tests/test_manifest.py` — source and lifecycle state regression tests.
- `tests/test_resume.py` — blocked recovery, transaction recovery, retry policy, and mutation fault tests.
- `tests/test_composition.py` — containment and all-or-nothing page publication tests.
- `tests/test_validation.py` — required final-artifact and guarded terminal-state tests.
- `tests/test_mcp_server.py` — exact 17-tool surface and full protocol lifecycle.
- `.github/workflows/tests.yml` — base/MCP split and Linux/macOS/Windows matrix with pinned actions.
- `README.md` — portable setup, truthful test commands, recovery, and MCP lifecycle.
- `references/workflow.md` — tested resume/finalization sequence.
- `references/capability-detection.md` — tested `BLOCKED` recovery behavior.
- `requirements.txt` — retain direct deterministic runtime pin.
- `requirements-mcp.txt` — retain MCP extra pin.

---

### Task 1: Shared source and path trust boundaries

**Files:**
- Create: `scripts/project_io.py`
- Create: `tests/test_project_io.py`
- Modify: `scripts/comic_sol.py:328-358,1290-1360`
- Modify: `scripts/validate_project.py:760-830`
- Modify: `scripts/compose_pages.py:30-46`
- Modify: `scripts/letter_panels.py` at every project-controlled path read
- Test: `tests/test_manifest.py`
- Test: `tests/test_composition.py`

**Interfaces:**
- Produces: `validate_source_bytes(source: bytes, suffix: str | None) -> str`
- Produces: `contained_project_path(project_dir: Path, relative: str | Path, *, must_exist: bool = False) -> Path`
- Consumed by: all later mutation, composition, validation, export, and MCP tasks.

- [ ] **Step 1: Write failing source-boundary tests**

Add tests proving rejection happens before project allocation:

```python
class SourceBoundaryTests(unittest.TestCase):
    def test_source_over_200_kib_creates_no_project(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(ValueError, "at most 200 KiB"):
                init_project(root, "Too Large", b"a" * (200 * 1024 + 1), {})
            self.assertEqual(list(root.iterdir()), [])

    def test_invalid_utf8_creates_no_project(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(ValueError, "UTF-8"):
                init_project(root, "Bad Encoding", b"\xff", {})
            self.assertEqual(list(root.iterdir()), [])
```

Add CLI tests with `.pdf` and `.json` sources; assert exit code `1` and no directory created. Add MCP test with a `200 * 1024 + 1` UTF-8 payload; assert `ToolError` and unchanged output root.

- [ ] **Step 2: Run source tests and verify RED**

Run:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_manifest.SourceBoundaryTests -v
```

Expected: FAIL because current `init_project()` accepts oversized and invalid UTF-8 bytes.

- [ ] **Step 3: Implement one source validator before allocation**

Create in `scripts/project_io.py`:

```python
MAX_SOURCE_BYTES = 200 * 1024
SOURCE_SUFFIXES = {".txt", ".md"}


def validate_source_bytes(source: bytes, suffix: str | None = None) -> str:
    if not isinstance(source, bytes):
        raise TypeError("source must be bytes")
    if len(source) > MAX_SOURCE_BYTES:
        raise ValueError("source must be at most 200 KiB as UTF-8 bytes")
    if suffix is not None and suffix.lower() not in SOURCE_SUFFIXES:
        raise ValueError("source file must use .txt or .md")
    try:
        return source.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("source must be valid UTF-8") from error
```

Call it in `init_project()` before `_allocate_project_directory()`. CLI passes `source_path.suffix`; MCP passes `None` because its input is already text.

- [ ] **Step 4: Write failing containment tests**

Cover absolute external PNG, `../`, sibling-prefix, symlink, and Windows-style drive paths:

```python
for bad in ("../outside.png", "/tmp/outside.png", "C:/outside.png"):
    with self.subTest(path=bad):
        with self.assertRaisesRegex(ValueError, "relative project path"):
            contained_project_path(project, bad)
```

Create a project symlink to an external file where supported. Assert rejection. On Windows, create a junction/reparse fixture when privileges permit; otherwise assert the lexical and resolved containment cases and keep a documented skip.

- [ ] **Step 5: Run containment tests and verify RED**

Run:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_project_io tests.test_composition -v
```

Expected: FAIL because composition currently accepts absolute manifest paths.

- [ ] **Step 6: Implement one contained-path resolver**

Use lexical rejection plus resolved containment:

```python
_DRIVE = re.compile(r"^[A-Za-z]:[/\\]")


def contained_project_path(
    project_dir: Path,
    relative: str | Path,
    *,
    must_exist: bool = False,
) -> Path:
    text = os.fspath(relative).replace("\\", "/")
    if not text or text.startswith("/") or _DRIVE.match(text) or ".." in text.split("/"):
        raise ValueError("path must be a relative project path")
    root = Path(project_dir).resolve(strict=True)
    candidate = root.joinpath(*PurePosixPath(text).parts).resolve(strict=must_exist)
    if candidate != root and root not in candidate.parents:
        raise ValueError("path escapes the project directory")
    current = candidate
    while current != root:
        if current.is_symlink():
            raise ValueError("project path must not contain symlinks")
        current = current.parent
    return candidate
```

Replace local containment implementations and `_artifact_path()` absolute-path support. Re-check containment immediately before opening each file.

- [ ] **Step 7: Run focused and full tests**

Run:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_project_io tests.test_manifest tests.test_composition \
  tests.test_validation tests.test_mcp_server -v
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest discover -s tests -v
```

Expected: focused PASS; full suite PASS.

- [ ] **Step 8: Commit**

```bash
git add scripts/project_io.py scripts/comic_sol.py scripts/validate_project.py \
  scripts/compose_pages.py scripts/letter_panels.py tests/test_project_io.py \
  tests/test_manifest.py tests/test_composition.py tests/test_validation.py \
  tests/test_mcp_server.py
git commit -m "fix: enforce shared source and project boundaries"
```

---

### Task 2: Cross-process project lock and durable atomic publication

**Files:**
- Modify: `scripts/project_io.py`
- Modify: `scripts/comic_sol.py:159-191`
- Modify: `scripts/export_pdf.py:158-200`
- Test: `tests/test_project_io.py`
- Test: `tests/test_concurrency.py`

**Interfaces:**
- Produces: `ProjectLock(project_dir: Path, timeout: float = 10.0)` context manager.
- Produces: `durable_atomic_write(path: Path, payload: bytes) -> None`.
- Produces: `fsync_directory(path: Path) -> None` with documented no-op fallback only where directory fsync is unsupported.
- Consumed by: Tasks 3–8.

- [ ] **Step 1: Write RED lock exclusion tests using subprocesses**

The parent process holds the lock; a child with a short timeout must fail:

```python
with ProjectLock(project, timeout=1.0):
    result = subprocess.run(
        [sys.executable, "-c", CHILD_LOCK_SCRIPT, os.fspath(project)],
        text=True,
        capture_output=True,
        check=False,
    )
self.assertEqual(result.returncode, 2)
self.assertIn("project is locked", result.stderr)
```

Add a second test proving the child succeeds after release. Use real subprocesses, not threads.

- [ ] **Step 2: Run lock tests and verify RED**

Run:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_concurrency.ProjectLockTests -v
```

Expected: ERROR because `ProjectLock` does not exist.

- [ ] **Step 3: Implement stdlib cross-platform lock**

`ProjectLock` opens `<project>/.comic-sol.lock`, writes sanitized PID metadata, and retries until timeout. Use `fcntl.flock(..., LOCK_EX | LOCK_NB)` on POSIX and `msvcrt.locking(..., LK_NBLCK, 1)` on Windows. Always unlock and close in `__exit__`; do not delete the lock file.

Public interface:

```python
class ProjectLock:
    def __init__(self, project_dir: Path, timeout: float = 10.0): ...
    def __enter__(self) -> "ProjectLock": ...
    def __exit__(self, exc_type, exc, traceback) -> None: ...
```

Raise:

```python
TimeoutError("project is locked by another process")
```

- [ ] **Step 4: Write RED syscall-order durability test**

Patch only syscall boundaries and assert this order:

```text
write → file flush → file fsync → os.replace → parent directory fsync
```

Also inject `os.replace` failure and assert temporary file cleanup plus original destination bytes unchanged.

- [ ] **Step 5: Run durability tests and verify RED**

Run:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_project_io.DurableWriteTests -v
```

Expected: FAIL because current writer never fsyncs parent directory.

- [ ] **Step 6: Implement durable writer and adopt it**

Implement:

```python
def fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def durable_atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
        fsync_directory(path.parent)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
```

Keep `atomic_write_bytes()` as a compatibility wrapper calling this function. Use same primitive for final PDF publication.

- [ ] **Step 7: Run focused and full tests**

Run:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_project_io tests.test_concurrency tests.test_export_pdf -v
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest discover -s tests -v
```

Expected: all PASS.

- [ ] **Step 8: Commit**

```bash
git add scripts/project_io.py scripts/comic_sol.py scripts/export_pdf.py \
  tests/test_project_io.py tests/test_concurrency.py tests/test_export_pdf.py
git commit -m "fix: lock projects and durably publish artifacts"
```

---

### Task 3: Race-free retry accounting and promotion archives

**Files:**
- Modify: `scripts/comic_sol.py:1058-1146`
- Modify: `scripts/mcp_server.py:158-183`
- Test: `tests/test_resume.py`
- Test: `tests/test_concurrency.py`

**Interfaces:**
- Consumes: `ProjectLock`, `contained_project_path`, `durable_atomic_write`.
- Preserves: `record_generation_attempt(...) -> dict[str, int]`.
- Preserves: `promote_attempt(...) -> Path`.

- [ ] **Step 1: Write RED policy tests**

Add separate tests rejecting:

- second initial attempt;
- second transient repeat;
- third visual retry;
- corrupt raster;
- raster smaller than 512×512;
- ninth global extra call.

For each rejection, assert `generation-counters.json` bytes are unchanged.

- [ ] **Step 2: Verify policy tests fail correctly**

Run:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_resume.ResumeTests.test_retry_budgets_and_transient_accounting -v
```

Expected: FAIL because current implementation permits repeated initial and transient attempts and counts unreadable files.

- [ ] **Step 3: Implement minimal locked policy**

Inside one `ProjectLock`:

1. resolve and decode raster;
2. read counters;
3. validate all per-panel/global limits;
4. increment;
5. durably write counters;
6. append sanitized `generation.attempt-recorded` event.

Exact limits:

```python
limits = {"initial": 1, "transient_repeat": 1, "visual_retry": 2}
```

No counter changes occur before raster and budget validation pass.

- [ ] **Step 4: Write RED 20-process budget test**

Create eight panels with one valid initial attempt each. Start 20 subprocesses behind a filesystem barrier, each attempting a distinct or repeated extra call. Assert exactly eight successes, twelve budget failures, and persisted global count `8`.

- [ ] **Step 5: Run concurrency test and verify RED**

Run:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_concurrency.RetryCounterProcessTests -v
```

Expected before lock integration: more than eight successes or persisted count below successes.

- [ ] **Step 6: Write RED promotion archive race test**

Seed accepted `p01-01.png`, then launch two promotions concurrently. Assert:

- accepted destination equals exactly one new attempt;
- archives are unique and immutable;
- old accepted bytes exist in exactly one archive;
- displaced concurrent version is either archived or rejected with stable conflict error;
- no archive is overwritten.

- [ ] **Step 7: Implement promotion under project lock**

Within one lock, select archive name, publish archive, then accepted destination. Use deterministic numeric archive allocation under the lock. Append `generation.attempt-promoted` event only after publication succeeds.

- [ ] **Step 8: Run focused, protocol, and full tests**

Run:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_resume tests.test_concurrency tests.test_mcp_server -v
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest discover -s tests -v
```

Expected: all PASS.

- [ ] **Step 9: Commit**

```bash
git add scripts/comic_sol.py scripts/mcp_server.py tests/test_resume.py \
  tests/test_concurrency.py tests/test_mcp_server.py
git commit -m "fix: serialize generation budgets and promotions"
```

---

### Task 4: Rollback-capable transactions and all-or-nothing composition

**Files:**
- Modify: `scripts/project_io.py`
- Modify: `scripts/compose_pages.py:99-179`
- Test: `tests/test_project_io.py`
- Test: `tests/test_composition.py`

**Interfaces:**
- Produces: `ProjectTransaction(project_dir: Path, operation: str)`.
- Produces methods: `stage_bytes(relative: str, payload: bytes)`, `commit()`, `recover(project_dir: Path)`.
- Consumed by: mutation consistency in Task 7.

- [ ] **Step 1: Write RED mixed-page regression**

Seed two valid old pages. Make page-2 source corrupt. Run `compose_all_pages()`. Assert both old page hashes remain unchanged and no new page is visible.

- [ ] **Step 2: Verify RED**

Run:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_composition.CompositionTests.test_failed_second_page_preserves_entire_prior_page_set -v
```

Expected: FAIL because page 1 is currently replaced before page 2 decode fails.

- [ ] **Step 3: Pre-render every page before publication**

Change `compose_all_pages()` to resolve and decode all sources, render all payloads into memory or project-local staging, then publish only after every page succeeds. Do not call `compose_page()` in a publication loop.

Desired structure:

```python
payloads = [
    (f"pages/page-{number:03d}.png", _compose_to_bytes(page, sources, settings))
    for number, page, sources in prepared_pages
]
with ProjectTransaction(project_dir, "composition") as transaction:
    for relative, payload in payloads:
        transaction.stage_bytes(relative, payload)
    transaction.commit()
```

- [ ] **Step 4: Write RED transaction failure tests**

Inject failure on second publish and simulated process interruption after first replacement. Assert `recover(project)` restores either complete old set or complete new set; never mixed.

Journal schema:

```json
{
  "operation": "composition",
  "phase": "publishing",
  "schema_version": "1.0",
  "targets": [
    {"path": "pages/page-001.png", "backup": "...", "staged": "..."}
  ]
}
```

Paths in journal remain project-relative.

- [ ] **Step 5: Implement minimal transaction**

`ProjectTransaction`:

- acquires `ProjectLock`;
- creates `logs/transactions/<id>/`;
- stores staged files and backups beneath transaction directory;
- durably writes canonical journal before first destination replace;
- updates phase after publish;
- restores backups in reverse order on caught failure;
- `recover()` inspects journals and rolls back any non-committed transaction;
- removes committed/rolled-back transaction directory after directory fsync.

Do not build a general database or nested transaction system.

- [ ] **Step 6: Run focused and full tests**

Run:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_project_io tests.test_composition -v
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest discover -s tests -v
```

Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
git add scripts/project_io.py scripts/compose_pages.py \
  tests/test_project_io.py tests/test_composition.py
git commit -m "fix: publish composed page sets transactionally"
```

---

### Task 5: Fail-closed final validation and guarded terminal operations

**Files:**
- Modify: `scripts/validate_project.py:842-1053`
- Modify: `scripts/comic_sol.py:432-477`
- Modify: `scripts/export_pdf.py`
- Create: `templates/page-qa.json`
- Create: `tests/test_finalization.py`
- Test: `tests/test_validation.py`
- Test: `tests/test_export_pdf.py`
- Test: `tests/test_manifest.py`

**Interfaces:**
- Produces: `require_valid_project(project_dir: Path, stage: str) -> None`.
- Produces: `guarded_export(project_dir: Path) -> Path` in engine layer.
- Terminal transition calls final validator before publishing manifest.

- [ ] **Step 1: Write RED missing-artifact matrix**

Build an otherwise terminal fixture, then separately remove or omit descriptor/file for:

- character bible;
- story plan;
- storyboard;
- each panel QA record;
- each raw/clean panel;
- each lettered panel;
- each `qa/pages/page-NNN.json` page-integrity record;
- each page PNG;
- `qa/report.md`;
- PDF;
- stage cache entry.

Assert `validate_project(project, "final")` reports the exact missing path/descriptor. Start with the reproduced empty `artifacts={}` case.

- [ ] **Step 2: Verify final validator RED**

Run:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_finalization.FinalArtifactTests -v
```

Expected: FAIL because an empty descriptor map currently returns no final artifact issue.

- [ ] **Step 3: Implement required final artifact enumeration**

Derive required paths from manifest page/panel counts and canonical layout, not from existing descriptor keys. Require semantic descriptors in `manifest.artifacts`; require panel QA/raw/clean/lettered, pages, report, PDF, and cache paths to exist and hash-match their owning records/cache.

Add the minimum Integrity Core page record at `qa/pages/page-NNN.json`:

```json
{
  "page": 1,
  "page_path": "pages/page-001.png",
  "page_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "schema_version": "1.0",
  "status": "reviewed"
}
```

The repeated `a` value is a concrete schema example only; implementation writes the actual page hash. Validation requires exact keys, canonical page/path agreement, `status == "reviewed"`, existing PNG, and matching SHA-256. This record proves a human/agent review was bound to the current page but does not invent detailed visual evidence. Detailed clipped-text, obstruction, reading-order, watermark, and border checks remain in Comic Quality milestone.

Add helper:

```python
def require_valid_project(project_dir: Path, stage: str) -> None:
    issues = validate_project(project_dir, stage)
    if issues:
        raise ProjectValidationError(issues)
```

- [ ] **Step 4: Write RED guarded transition/export tests**

Cases:

- unresolved panel failure;
- missing report;
- missing PDF descriptor;
- stale page hash;
- status `EXPORTED` followed by `transition(..., "COMPLETE")`;
- export attempt with invalid panel QA.

Assert rejection and unchanged prior PDF/manifest bytes.

- [ ] **Step 5: Verify guarded operations RED**

Run:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_finalization.GuardedOperationTests -v
```

Expected: FAIL because transition and export currently bypass final quality gates.

- [ ] **Step 6: Implement minimal guarded operations**

Rules:

- Add validator stage `export-ready`. It requires current planning, storyboard, panel QA, raw/clean/lettered panels, page PNGs, page-integrity records, and composition cache, but deliberately does not require report, PDF, or export cache.
- `guarded_export()` requires `export-ready` validation, composes no hidden stages, writes PDF transactionally, verifies PDF, and records descriptor only after success.
- Transition to `COMPLETE` or `COMPLETE_WITH_WARNINGS` calls `require_valid_project(project, "final")` before any event or manifest write.
- Final validation permits `EXPORTED` during pre-terminal validation but still requires all final artifacts.
- A failure does not replace valid PDF or terminal manifest.

- [ ] **Step 7: Run focused and full tests**

Run:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_finalization tests.test_validation tests.test_export_pdf \
  tests.test_manifest -v
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest discover -s tests -v
```

Expected: all PASS.

- [ ] **Step 8: Commit**

```bash
git add scripts/validate_project.py scripts/comic_sol.py scripts/export_pdf.py \
  templates/page-qa.json \
  tests/test_finalization.py tests/test_validation.py tests/test_export_pdf.py \
  tests/test_manifest.py
git commit -m "fix: fail closed on export and terminal validation"
```

---

### Task 6: Recoverable BLOCKED state and actionable resume

**Files:**
- Modify: `scripts/comic_sol.py:432-477,896-1046,1290-1410`
- Modify: `templates/manifest.json`
- Test: `tests/test_manifest.py`
- Test: `tests/test_resume.py`

**Interfaces:**
- Produces: `block_project(project_dir: Path, reason: str, warning: str) -> dict[str, object]`.
- Produces: `resume_project(project_dir: Path) -> dict[str, object]`.
- Preserves: `build_resume_plan(project_dir) -> list[ResumeAction]`.

- [ ] **Step 1: Write RED BLOCKED recovery end-to-end test**

Progress fixture to `STORYBOARDED`, block for `image-capability-unavailable`, restore capability field, call `resume_project()`, and assert:

- status returns to `STORYBOARDED` or the last valid later state;
- valid planning/storyboard artifacts stay byte-identical;
- only resolved warning is removed;
- next action identifies generation as agent-required;
- no manual manifest edit occurs in test.

- [ ] **Step 2: Verify RED**

Run:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_resume.BlockedRecoveryTests -v
```

Expected: ERROR or invalid transition because `BLOCKED` has no recovery path.

- [ ] **Step 3: Add explicit blocking metadata compatibly**

Add optional manifest fields validated only when status is `BLOCKED`:

```json
{
  "blocked_from": "STORYBOARDED",
  "blocked_reason": "image-capability-unavailable"
}
```

Old v1 manifests without fields remain readable unless they claim `BLOCKED`; legacy blocked fixtures derive conservative recovery from cache and receive canonical metadata on resume.

- [ ] **Step 4: Implement `block_project()` and `resume_project()`**

`block_project()` records last normal status and stable reason under lock. `resume_project()`:

1. recovers pending project transactions;
2. builds resume plan;
3. identifies earliest stale stage;
4. restores status from valid cache/artifacts;
5. clears only warning associated with resolved block;
6. runs deterministic invalidation when needed;
7. returns structured `status`, `preserved`, `invalidated`, and `next_action`.

Do not run agent-required image generation.

- [ ] **Step 5: Add CLI `resume` execution path**

Keep `resume-plan` diagnostic output. Add/route `resume` so output includes exact next command or `agent_required: generation` in JSON mode.

- [ ] **Step 6: Run focused and full tests**

Run:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_resume tests.test_manifest -v
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest discover -s tests -v
```

Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
git add scripts/comic_sol.py templates/manifest.json \
  tests/test_resume.py tests/test_manifest.py
git commit -m "feat: resume blocked projects safely"
```

---

### Task 7: Transactional consistency for project mutations

**Files:**
- Modify: `scripts/comic_sol.py:447-477,750-780,1015-1046,1149-1223`
- Modify: `scripts/project_io.py`
- Test: `tests/test_resume.py`
- Test: `tests/test_manifest.py`

**Interfaces:**
- Consumes: `ProjectLock`, `ProjectTransaction`.
- Mutation unit: related manifest/cache/QA/event outputs commit or roll back together.

- [ ] **Step 1: Write RED fault-injection tests for each boundary**

Inject failure after each staged output for:

- transition event/manifest;
- stage cache/event;
- invalidation cache/manifest;
- override QA/manifest/event.

For each, reopen project and call transaction recovery. Assert exact old state or exact new state; no contradictory mix and no duplicate event.

- [ ] **Step 2: Verify RED**

Run:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_resume.MutationTransactionTests \
  tests.test_manifest.ManifestTests.test_transition_publishes_manifest_only_after_event_succeeds -v
```

Expected: at least one contradictory state or missing recovery behavior.

- [ ] **Step 3: Stage canonical event bytes instead of appending mid-operation**

Add an internal event-record builder:

```python
def canonical_event_record(event: str, details: dict[str, object]) -> bytes:
    record = {
        "details": _sanitize_event_details(details),
        "event": event,
        "timestamp": _utc_now(),
    }
    return canonical_json_bytes(record) + b"\n"
```

For transaction-bound events, stage a replacement `events.jsonl` built from prior bytes plus one record. Retain `append_event()` only for standalone non-transaction callers under the project lock.

- [ ] **Step 4: Convert four mutations to project transactions**

Each function precomputes all canonical bytes, stages every destination, then commits once. Return values occur only after commit.

- [ ] **Step 5: Add subprocess termination recovery test**

Launch a child mutation with a test-only environment-controlled pause after journal publication, terminate it, run `ProjectTransaction.recover(project)`, and assert consistent state. Do not add test-only branches to public APIs; isolate pause hook behind an internal callable injected by the test process.

- [ ] **Step 6: Run focused and full tests**

Run:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_resume tests.test_manifest tests.test_project_io -v
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest discover -s tests -v
```

Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
git add scripts/comic_sol.py scripts/project_io.py \
  tests/test_resume.py tests/test_manifest.py tests/test_project_io.py
git commit -m "fix: commit project mutations transactionally"
```

---

### Task 8: Complete deterministic MCP lifecycle

**Files:**
- Modify: `scripts/render_report.py`
- Modify: `scripts/comic_sol.py`
- Modify: `scripts/mcp_server.py`
- Modify: `tests/test_mcp_server.py`
- Modify: `tests/test_finalization.py`

**Interfaces:**
- Produces: `render_report(project_dir: Path, final_status: str | None = None) -> Path`.
- Produces: `finalize_project(project_dir: Path) -> dict[str, object]`.
- Adds MCP tools: `comic_resume`, `comic_render_report`, `comic_finalize`.
- Exact MCP surface becomes 17 tools.

- [ ] **Step 1: Write RED exact-surface test**

Expected tool names:

```python
EXPECTED_TOOLS = {
    "comic_doctor", "comic_init", "comic_status", "comic_validate",
    "comic_resume_plan", "comic_resume", "comic_transition",
    "comic_invalidate", "comic_record_stage", "comic_record_attempt",
    "comic_promote_attempt", "comic_override_panel", "comic_letter",
    "comic_compose", "comic_render_report", "comic_export",
    "comic_finalize",
}
```

Assert exact equality, not subset.

- [ ] **Step 2: Verify surface RED**

Run:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_mcp_server.McpServerUnitTests.test_exposes_exact_approved_tool_surface -v
```

Expected: FAIL with three missing tools.

- [ ] **Step 3: Extract callable report renderer**

Refactor `render_report.py` so CLI and MCP call the same:

```python
def render_report(
    project_dir: Path,
    output: Path | None = None,
    final_status: str | None = None,
) -> Path:
    destination = output or Path(project_dir) / "qa/report.md"
    # Existing deterministic report construction uses final_status when supplied.
    durable_atomic_write(destination, payload)
    return destination
```

- [ ] **Step 4: Implement deterministic `finalize_project()`**

The function computes `COMPLETE` or `COMPLETE_WITH_WARNINGS` before rendering, then runs only deterministic stale stages in order under engine rules:

1. panel validation;
2. lettering if stale;
3. composition if stale;
4. guarded export;
5. report render with the computed terminal status, without mutating manifest early;
6. export stage record;
7. final validation;
8. guarded terminal transition.

If any `qa/pages/page-NNN.json` integrity record is absent or stale, return a stable `page_qa_required` failure rather than self-attesting visual evidence. Integrity Core must not fabricate QA.

- [ ] **Step 5: Add three thin MCP tools**

Each resolves project once, calls engine function, converts paths to project-relative POSIX strings, and converts expected errors to `ToolError` without leaking absolute paths.

- [ ] **Step 6: Expand real stdio protocol lifecycle test**

Start from `comic_init`, install deterministic fixture artifacts, invoke report/finalize, and assert:

- 17 tools discovered;
- PDF exists and decodes;
- report exists;
- export cache exists;
- final validator returns no issues;
- terminal status matches warning state.

- [ ] **Step 7: Run protocol and full tests**

Run:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_mcp_server tests.test_finalization -v
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest discover -s tests -v
```

Expected: all PASS.

- [ ] **Step 8: Commit**

```bash
git add scripts/render_report.py scripts/comic_sol.py scripts/mcp_server.py \
  tests/test_mcp_server.py tests/test_finalization.py
git commit -m "feat: complete deterministic MCP lifecycle"
```

---

### Task 9: Optional dependency truth, portable docs, and cross-platform CI

**Files:**
- Modify: `tests/test_mcp_server.py`
- Modify: `.github/workflows/tests.yml`
- Modify: `README.md`
- Modify: `references/workflow.md`
- Modify: `references/capability-detection.md`
- Modify: `requirements.txt`
- Modify: `requirements-mcp.txt`
- Test: `tests/test_validation.py`

**Interfaces:**
- Base install: Pillow only; MCP tests skip cleanly when `mcp` is absent.
- MCP-extra install: Pillow + MCP; all tests run.
- CI source-level platforms: Ubuntu, macOS, Windows.

- [ ] **Step 1: Write RED packaging/documentation contract tests**

Add assertions that:

- README contains no `/home/acer` or developer checkout path;
- README labels base and MCP-extra test commands separately;
- documented MCP command uses repository-relative development command only until portable CLI milestone;
- recovery docs name tested `resume` behavior;
- MCP tool count is 17;
- workflow contains Ubuntu, macOS, and Windows jobs and no `/tmp` path.

- [ ] **Step 2: Verify documentation contract RED**

Run:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_validation.PackagingTests -v
```

Expected: FAIL on machine-specific README paths and single-platform CI.

- [ ] **Step 3: Make MCP tests optional in base environment**

At the top of `tests/test_mcp_server.py`, use dependency detection without importing MCP first:

```python
MCP_AVAILABLE = importlib.util.find_spec("mcp") is not None

@unittest.skipUnless(MCP_AVAILABLE, "MCP extra is not installed")
class McpProtocolTests(unittest.IsolatedAsyncioTestCase):
    ...
```

Place MCP-dependent imports after detection or inside guarded scope. Unit tests that can import `mcp_server.py` also skip when absent.

- [ ] **Step 4: Prove base and MCP-extra environments separately**

Create temporary virtual environments outside the repo:

```bash
python3.11 -m venv /tmp/comic-sol-base
/tmp/comic-sol-base/bin/pip install -r requirements.txt
/tmp/comic-sol-base/bin/python -m unittest discover -s tests -v

python3.11 -m venv /tmp/comic-sol-mcp-extra
/tmp/comic-sol-mcp-extra/bin/pip install -r requirements.txt -r requirements-mcp.txt
/tmp/comic-sol-mcp-extra/bin/python -m unittest discover -s tests -v
```

Expected: base PASS with MCP classes skipped; extra PASS with no MCP skips.

- [ ] **Step 5: Split and expand GitHub Actions**

Use a matrix containing:

```yaml
strategy:
  fail-fast: false
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    extras: [base, mcp]
runs-on: ${{ matrix.os }}
```

Use Python `tempfile.gettempdir()` or `${{ runner.temp }}` for doctor output. Pin `actions/checkout` to `11bd71901bbe5b1630ceea73d27597364c9af683` (`v4.2.2`) and `actions/setup-python` to `a26af69be951a213d495a4c3e4e4022e16d87065` (`v5.6.0`). Base installs `requirements.txt`; MCP job adds `requirements-mcp.txt`.

Do not claim WSL/container gates here; add explicit smoke jobs only if runners are available in this milestone. README distinguishes continuously tested native platforms from planned WSL/container release gates.

- [ ] **Step 6: Rewrite machine-neutral README and recovery docs**

Development MCP example derives paths from current checkout and selected output root. It does not hardcode a username, home, or obsolete repo. Document tested full lifecycle and exact current limitations.

- [ ] **Step 7: Run local contract, base, MCP, and full gates**

Run:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest \
  tests.test_validation tests.test_mcp_server -v
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest discover -s tests -v
git diff --check
```

Then push branch and require all matrix jobs green before merge.

- [ ] **Step 8: Commit**

```bash
git add tests/test_mcp_server.py tests/test_validation.py \
  .github/workflows/tests.yml README.md references/workflow.md \
  references/capability-detection.md requirements.txt requirements-mcp.txt
git commit -m "ci: verify base and MCP workflows across platforms"
```

---

### Task 10: Integrity Core end-to-end gate and independent review

**Files:**
- Modify only files required by verified review findings.
- Test: entire `tests/` suite.

**Interfaces:**
- Consumes all prior task interfaces.
- Produces current evidence for Integrity Core acceptance; no new product behavior.

- [ ] **Step 1: Run static and syntax gates**

```bash
python3.11 -m compileall -q scripts tests
git diff --check
```

Expected: exit `0`, no output from `git diff --check`.

- [ ] **Step 2: Run base suite from clean environment**

```bash
python3.11 -m venv /tmp/comic-sol-integrity-base
/tmp/comic-sol-integrity-base/bin/pip install -r requirements.txt
/tmp/comic-sol-integrity-base/bin/python -m unittest discover -s tests -v
```

Expected: PASS; MCP-extra tests skipped with documented reason only.

- [ ] **Step 3: Run MCP-extra suite from clean environment**

```bash
python3.11 -m venv /tmp/comic-sol-integrity-mcp
/tmp/comic-sol-integrity-mcp/bin/pip install -r requirements.txt -r requirements-mcp.txt
/tmp/comic-sol-integrity-mcp/bin/python -m unittest discover -s tests -v
```

Expected: PASS; real stdio lifecycle test discovers exactly 17 tools.

- [ ] **Step 4: Run explicit high-risk regressions**

```bash
/tmp/comic-sol-integrity-mcp/bin/python -m unittest \
  tests.test_concurrency \
  tests.test_finalization \
  tests.test_project_io \
  tests.test_resume \
  tests.test_composition \
  tests.test_mcp_server -v
```

Expected: PASS with real subprocess concurrency and protocol tests.

- [ ] **Step 5: Run doctor with platform-neutral temp root**

```bash
/tmp/comic-sol-integrity-mcp/bin/python - <<'PY'
import subprocess, sys, tempfile
from pathlib import Path
root = Path(tempfile.mkdtemp(prefix="comic-sol-doctor-"))
raise SystemExit(subprocess.call([
    sys.executable, "scripts/comic_sol.py", "doctor", "--output-root", str(root)
]))
PY
```

Expected: all deterministic runtime checks PASS.

- [ ] **Step 6: Obtain independent blocker-only review**

Review exact diff from `9b15ef1` to current head for:

- containment and symlink/reparse escape;
- lock/process races;
- transaction rollback/recovery;
- final validation omissions;
- lifecycle bypasses;
- base/MCP test truthfulness;
- cross-platform breakage;
- docs accuracy.

Reviewer returns READY or exact file:line blockers. Fix blockers through new RED-GREEN cycles, maximum two review loops before reassessing architecture.

- [ ] **Step 7: Re-run all gates after final change**

Repeat Steps 1–5 from fresh environments. Historical green evidence is invalid after any review fix.

- [ ] **Step 8: Commit review fixes, push, and open private PR**

```bash
git add -A
git status --short
git diff --cached --check
git commit -m "fix: close Integrity Core review blockers"
git push origin HEAD
gh pr create --repo wenn-id/comic-sol-lab \
  --base ai/post-event-development \
  --head ai/integrity-core \
  --title "feat: harden Comic Sol Integrity Core" \
  --body $'## Summary\n- close all 13 audited Integrity Core defects\n- add fail-closed finalization and recoverable project mutations\n- verify base and MCP workflows across native CI platforms\n\n## Verification\n- clean base suite: PASS\n- clean MCP-extra suite and 17-tool lifecycle: PASS\n- concurrency and fault-injection suites: PASS'
```

Expected: private PR created; all required CI jobs green. Do not merge while any gate is pending or red.

---

## Defect-to-Task Traceability

| Audited defect | Task |
|---|---|
| Final validation accepts missing artifacts | 5 |
| Export/terminal transition bypasses gates | 5 |
| Retry counter race and false accounting | 2–3 |
| Composition reads external paths | 1 |
| Multi-page partial overwrite | 4 |
| Project mutation contradictions | 4, 7 |
| Promotion archive race | 3 |
| `BLOCKED` cannot resume | 6 |
| Source limits bypassed by CLI/MCP | 1 |
| MCP lacks report/final lifecycle | 8 |
| Optional MCP breaks base suite | 9 |
| Machine-specific documentation | 9 |
| Advertised platforms not continuously checked | 9–10 |

## Integrity Core Exit Gate

Integrity Core is complete only when:

- all 13 defect rows have a regression test that was observed RED before the fix;
- base clean install passes without MCP SDK;
- MCP-extra clean install passes with real stdio lifecycle;
- concurrency tests prove exact budgets across processes;
- fault tests prove all-or-nothing project mutations;
- final validation rejects every missing/stale required artifact;
- `BLOCKED` recovery completes without manual manifest edits;
- all supported source-level OS CI jobs are green;
- independent review returns READY;
- public submission repository remains unchanged.

Installer, provider, client auto-configuration, full page-QA schema, typography expansion, full-content PDF comparison, four-panel layout, and broad sample matrix receive separate plans after this gate.

## Execution Choice

1. **Subagent-Driven (recommended)** — one fresh worker per task, RED-GREEN evidence and review between tasks.
2. **Inline Execution** — execute task batches in this session with checkpoints.

No implementation starts until the user selects one execution mode.
