# Comic Sol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an installable Comic Sol Agent Skill that turns one natural-language request or UTF-8 text/Markdown story into editable comic artifacts, visually reviewed panel PNGs, deterministic lettered page PNGs, a PDF, a manifest, and a human-readable QA report.

**Architecture:** The agent plane in `SKILL.md` and progressively disclosed references owns semantic planning, capability detection, image generation, and visual judgment. Versioned JSON and PNG artifacts are the boundary to six deterministic Python scripts that initialize and validate state, calculate fixed layouts, resume safely, letter panels, compose pages, export PDF, and render QA without calling an LLM or image API.

**Tech Stack:** Portable Agent Skills conventions; Codex with GPT-5.6 Sol as the primary host; Python 3.11 standard library; Pillow 11.3.0; `unittest`; UTF-8 JSON/Markdown; PNG and raster PDF.

## Global Constraints

- Product form is a pure installable skill: no web app, server, dashboard, SaaS, database, authentication, frontend, or provider-specific API adapter.
- Deterministic scripts never call an LLM, image model, network API, provider SDK, or secret-bearing environment variable.
- Python is 3.11; Pillow is pinned to `11.3.0`; Pillow is the only non-stdlib dependency.
- Tests use `unittest`, run offline, use synthetic images/fixtures, and make no image-generation calls.
- Every JSON artifact uses schema version `"1.0"`, UTF-8, two-space indentation, sorted keys, and one newline at EOF; unknown fields are rejected.
- IDs match `^[a-z][a-z0-9-]{0,47}$`; timestamps are ISO 8601 UTC.
- Must-have output is 1–4 pages, at most 12 panels total and 4 panels per page, left-to-right, RGB 1600 × 2400 px, 64 px outer margin, and 32 px gutter.
- Layouts are exactly `full-page`, `two-horizontal`, `three-horizontal`, `hero-top-two-bottom`, and `two-top-hero-bottom`; no overlap, rotation, bleed, or inset panels.
- Lettering uses bundled `assets/fonts/NotoSans-Regular.ttf`; dialogue/caption starts at 42 px and steps by 2 px to 24 px; SFX starts at 64 px and steps to 24 px.
- Dialogue is at most 32 words per item, captions 45, SFX 3, and a panel contains at most 3 text items and 45 total words.
- Generation permits 2 visual regenerations per panel and 8 extra calls project-wide after initial reference/panel calls; transient repeats share the global cap.
- One natural-language invocation must complete the happy path without manual commands or confirmation when defaults are safe and a compatible image capability is present.
- Image generation is selected from agent-exposed capabilities by feature detection; no hardcoded image API, token, credential, or provider is permitted.
- Generated dialogue is forbidden; bubbles, captions, and SFX are rendered deterministically after panel acceptance.
- Original manga/anime direction is described with visual traits; prompts do not imitate living artists, active studios, or named franchises.
- Scope is fixed to the approved design at `docs/superpowers/specs/2026-07-18-comic-sol-design.md`; stretch work begins only after all must-have gates pass.

---

## 1. Fixed file inventory

Tags indicate the expected review weight: **Q** = quick contract/content file, **P** = primary behavior or substantial test surface, **V** = verification/evidence artifact. Directories are listed where the spec names a directory boundary; generated comic projects are runtime outputs and are not added to the package inventory.

| Tag | Path | Fixed responsibility |
|---|---|---|
| Q | `SKILL.md` | Trigger frontmatter, natural-language entry, state-machine orchestration, progressive reference routing |
| Q | `LICENSE` | Repository license covering original source and documentation |
| V | `README.md` | Install, support, test, demo, collaboration, limitations, sample-output and Build Week evidence |
| Q | `references/` | Progressively disclosed agent contracts and policy documentation |
| Q | `references/workflow.md` | Ten-stage agent procedure, input modes, gates, failure/resume/completion UX |
| Q | `references/creative-direction.md` | Story/character/storyboard authoring, exact prompt-anchor order, originality rules |
| Q | `references/capability-detection.md` | Feature-based tool selection, raster contract, degradation and unavailable-capability message |
| Q | `references/visual-qa.md` | Seven checks, severity/decision policy, correction clauses, retry/override rules |
| Q | `references/safety-ip.md` | Privacy, secret warning, IP transformation, content refusal, logging restrictions |
| P | `references/schemas.md` | Normative version 1.0 manifest, character, story, storyboard, panel QA and report contracts |
| P | `scripts/` | Exactly six deterministic Python entry points; no model/network layer |
| P | `scripts/comic_sol.py` | CLI, initialization, atomic JSON/events, hashing, transitions, cache keys, invalidation, retry accounting, status/resume/doctor |
| P | `scripts/validate_project.py` | Strict schema, file/hash, cross-reference, text, geometry, image and project-integrity validation |
| P | `scripts/compose.py` | RGB page composition, exact panel placement/resampling, inward borders and ordered PNG output |
| P | `scripts/lettering.py` | Normalization/crop, glyph checks, wrapping, zones, bubbles/captions/tails/SFX, overflow errors |
| P | `scripts/export_pdf.py` | Ordered page discovery, validation and 150-DPI raster PDF export |
| P | `scripts/render_report.py` | Deterministic Markdown QA aggregation and seven-section template rendering |
| Q | `templates/` | Canonical version 1.0 artifact starting points and report template |
| Q | `templates/manifest.json` | Minimal valid manifest skeleton with settings/stage versions and absent future artifacts |
| Q | `templates/character-bible.json` | Empty valid `characters` collection |
| Q | `templates/story-plan.json` | Structurally valid story-plan shape copied for agent population |
| Q | `templates/storyboard.json` | Empty valid `pages` collection copied for agent population |
| Q | `templates/panel-record.json` | Seven-check panel QA shape copied per panel |
| Q | `templates/qa-report.md.tmpl` | Required human-readable report section tokens |
| Q | `assets/` | Redistributable deterministic runtime assets only |
| Q | `assets/fonts/` | Pinned font boundary |
| P | `assets/fonts/NotoSans-Regular.ttf` | Bundled Latin/Greek/Cyrillic font used by tests and production lettering |
| V | `assets/README.md` | Noto Sans provenance, license, version, SHA-256, supported glyph scope |
| V | `tests/` | Offline deterministic test suite |
| V | `tests/fixtures/` | Synthetic valid and interrupted projects; no generated or copyrighted art |
| V | `tests/test_manifest.py` | Initialization, state, hashing, atomic writes, retry and doctor tests |
| V | `tests/test_validation.py` | Strict schemas, limits, references, five layouts and integrity tests |
| V | `tests/test_lettering.py` | Text sanitation, fitting, geometry, drawing and error tests |
| V | `tests/test_compose.py` | Page sizing, ordering, resizing, borders and stable pixel tests |
| V | `tests/test_export_pdf.py` | Page discovery/order, RGB PDF, page count and failure tests |
| V | `tests/test_resume.py` | Cache-key, invalidation, idempotency and selective-repair tests |
| V | `tests/test_report.py` | QA aggregation, disclosures, warnings, overrides and integration fixture tests |

No additional production module is introduced. Shared deterministic helpers stay in `scripts/comic_sol.py` and are imported by sibling scripts after adding `scripts/` to `sys.path` in tests. This honors the fixed six-script boundary in the design.

## 2. Dependency graph and build order

```text
T01 contracts/assets/templates
 ├─> T02 lifecycle CLI ───────────────┐
 ├─> T03 strict validation/layout ────┤
 │                                    ├─> T04 resume/retry/cache
 ├─> T05 lettering ───────────────────┤
 ├─> T06 composition ─────────────────┤
 ├─> T07 PDF export ──────────────────┤
 └─> T08 QA report ───────────────────┘
                                      ├─> T09 agent skill/references
                                      ├─> T10 integration fixtures/full suite
                                      └─> T11 packaging/evidence
                                           └─> T12 live acceptance/demo gate
                                                └─> S01–S05 stretch, if eligible
```

### File-level dependencies

| File | Direct dependencies |
|---|---|
| `templates/*.json` | `references/schemas.md`, schema version `1.0` |
| `scripts/comic_sol.py` | `templates/*.json`, `assets/fonts/NotoSans-Regular.ttf`, stdlib, Pillow only for `doctor`/image verification |
| `scripts/validate_project.py` | `scripts/comic_sol.py` canonical JSON/hash/layout helpers, `references/schemas.md`, Pillow |
| `scripts/lettering.py` | `scripts/comic_sol.py` atomic write helpers, validated storyboard/panel records, bundled font, Pillow |
| `scripts/compose.py` | `scripts/comic_sol.py` atomic helpers, validated storyboard, lettered panels, Pillow |
| `scripts/export_pdf.py` | `scripts/comic_sol.py` atomic helpers, composed page PNGs, Pillow |
| `scripts/render_report.py` | `scripts/comic_sol.py` canonical read/write helpers, validated manifest/panel records, report template |
| `references/workflow.md` | stable CLI commands from T02–T08; capability/QA/safety references |
| `references/creative-direction.md` | character/story/storyboard schemas and prompt contract |
| `references/capability-detection.md` | manifest capability fields, image verification CLI, blocked transition |
| `references/visual-qa.md` | panel record schema, retry accounting/attempt promotion commands |
| `references/safety-ip.md` | workflow logging/prompt rules |
| `SKILL.md` | all six references and stable script CLI surface |
| `README.md` | `SKILL.md`, `doctor`, full offline suite, clean-room and live acceptance results |
| `tests/fixtures/` | templates plus T02–T08 public interfaces; generated by deterministic test helpers and committed |

Build in task order. T05–T08 may be implemented independently after T01–T03, but each must merge only after its focused tests and the accumulated suite pass.

## 3. TDD task breakdown

### Task T01: Freeze schemas, templates, and the licensed font asset

**Files:**

- Create: `references/schemas.md`
- Create: `templates/manifest.json`
- Create: `templates/character-bible.json`
- Create: `templates/story-plan.json`
- Create: `templates/storyboard.json`
- Create: `templates/panel-record.json`
- Create: `templates/qa-report.md.tmpl`
- Create: `assets/fonts/NotoSans-Regular.ttf`
- Create: `assets/README.md`
- Create: `tests/test_validation.py`

**Interfaces:**

- Produces six schema `1.0` JSON templates readable with `json.load`.
- Defines manifest statuses `INIT`, `PLANNED`, `SCRIPTED`, `STORYBOARDED`, `REFERENCES_READY`, `PANELS_READY`, `QA_READY`, `LETTERED`, `COMPOSED`, `EXPORTED`, `COMPLETE`, `BLOCKED`, `COMPLETE_WITH_WARNINGS`.
- Defines exact enums/required fields from design Section 8, seven panel check IDs, five layout names, eight anchors, word/panel/page limits, and report tokens `{{PROJECT_SUMMARY}}`, `{{CAPABILITY}}`, `{{COUNTS}}`, `{{PANEL_TABLE}}`, `{{WARNINGS}}`, `{{INTEGRITY}}`, `{{RESUME}}`.
- Bundles the regular static Noto Sans TTF from the official Noto Sans release, preserving its upstream license; `assets/README.md` records upstream URL, upstream license name, local filename, SHA-256 obtained from the committed bytes, and Latin/Greek/Cyrillic support scope.

- [ ] **Step 1: Write the failing template/font contract test**

Add this complete first test to `tests/test_validation.py`:

```python
import hashlib
import json
import unittest
from pathlib import Path

from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[1]


class TemplateContractTests(unittest.TestCase):
    def test_templates_are_canonical_v1_and_font_is_loadable(self):
        names = (
            "manifest.json", "character-bible.json", "story-plan.json",
            "storyboard.json", "panel-record.json",
        )
        for name in names:
            raw = (ROOT / "templates" / name).read_bytes()
            self.assertTrue(raw.endswith(b"\n"), name)
            data = json.loads(raw)
            self.assertEqual("1.0", data["schema_version"])
            expected = (json.dumps(data, ensure_ascii=False, indent=2,
                                   sort_keys=True) + "\n").encode("utf-8")
            self.assertEqual(expected, raw, name)

        font_path = ROOT / "assets/fonts/NotoSans-Regular.ttf"
        ImageFont.truetype(str(font_path), 42)
        digest = hashlib.sha256(font_path.read_bytes()).hexdigest()
        asset_notes = (ROOT / "assets/README.md").read_text("utf-8")
        self.assertIn(digest, asset_notes)
        self.assertIn("SIL Open Font License", asset_notes)
```

- [ ] **Step 2: Run the test and confirm the red state**

Run: `python3.11 -m unittest tests.test_validation.TemplateContractTests -v`

Expected: exit `1` with `FileNotFoundError` for `templates/manifest.json` or `assets/fonts/NotoSans-Regular.ttf`; no network call occurs.

- [ ] **Step 3: Add the minimal contracts and assets**

Write the six JSON/template files from spec Section 8 with real empty/initial values rather than sentinel hashes. Use this command after authoring each JSON file to canonicalize it mechanically:

```bash
python3.11 -c 'import json,pathlib,sys; p=pathlib.Path(sys.argv[1]); d=json.loads(p.read_text("utf-8")); p.write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")' templates/manifest.json
```

Repeat the command for the other four JSON templates. `templates/qa-report.md.tmpl` is Markdown and contains the seven named tokens in report-section order. Add all field tables and cross-field rules to `references/schemas.md`. Obtain the official static `NotoSans-Regular.ttf`, retain its actual bytes, and compute its recorded digest with `sha256sum assets/fonts/NotoSans-Regular.ttf`; do not substitute a system font or rename another font.

- [ ] **Step 4: Verify the focused contract**

Run: `python3.11 -m unittest tests.test_validation.TemplateContractTests -v`

Expected: `Ran 1 test` and `OK`.

- [ ] **Step 5: Commit the contract boundary**

```bash
git add references/schemas.md templates assets tests/test_validation.py
git commit -m "feat: define Comic Sol artifact contracts"
```

### Task T02: Implement project initialization, state transitions, atomic I/O, and doctor

**Files:**

- Create: `scripts/comic_sol.py`
- Create: `tests/test_manifest.py`
- Modify: `tests/test_validation.py`

**Interfaces:**

```python
def canonical_json_bytes(value: object) -> bytes: ...
def read_json(path: Path) -> dict[str, object]: ...
def atomic_write_bytes(path: Path, payload: bytes) -> None: ...
def atomic_write_json(path: Path, value: object) -> None: ...
def sha256_file(path: Path) -> str: ...
def slugify(title: str) -> str: ...
def layout_rects(name: str) -> list[dict[str, int]]: ...
def rectangles_overlap(a: dict[str, int], b: dict[str, int]) -> bool: ...
def init_project(output_root: Path, title: str, source: bytes,
                 request: dict[str, object]) -> Path: ...
def transition(project_dir: Path, target: str,
               warning: str | None = None) -> dict[str, object]: ...
def append_event(project_dir: Path, event: str,
                 details: dict[str, object]) -> None: ...
def doctor(output_root: Path) -> tuple[bool, list[str]]: ...
def main(argv: list[str] | None = None) -> int: ...
```

CLI surface:

```text
comic_sol.py init --output-root PATH --title TITLE --source PATH --request-json PATH
comic_sol.py transition PROJECT_DIR TARGET [--warning TEXT]
comic_sol.py status PROJECT_DIR [--json]
comic_sol.py doctor [--output-root PATH]
```

`init_project` creates the complete generated-directory skeleton, exact `source/input.txt`, canonical `source/request.json`, and `project.json`, using exclusive slug allocation. `transition` permits only the linear state machine plus transitions to `BLOCKED` and terminal `COMPLETE_WITH_WARNINGS`; it atomically writes the manifest last.

- [ ] **Step 1: Write failing lifecycle tests**

Create `tests/test_manifest.py` with imports through `sys.path.insert(0, str(ROOT / "scripts"))` and these test cases:

```python
class ManifestTests(unittest.TestCase):
    def test_init_preserves_source_and_uses_suffix_without_overwrite(self):
        request = {"mode": "short_prompt", "language": "en"}
        first = init_project(self.root, "Sunlight Courier", b"A courier.", request)
        second = init_project(self.root, "Different Request", b"Different.", request)
        self.assertEqual("sunlight-courier", first.name)
        self.assertEqual("different-request", second.name)
        self.assertEqual(b"A courier.", (first / "source/input.txt").read_bytes())
        self.assertEqual("INIT", read_json(first / "project.json")["status"])

    def test_transition_rejects_skips_and_writes_manifest_last(self):
        project = init_project(self.root, "Story", b"Story", {"mode": "short_prompt", "language": "en"})
        with self.assertRaisesRegex(ValueError, "INIT.*STORYBOARDED"):
            transition(project, "STORYBOARDED")
        result = transition(project, "PLANNED")
        self.assertEqual("PLANNED", result["status"])

    def test_canonical_json_is_sorted_compact_utf8_without_timestamp_rules(self):
        self.assertEqual(b'{"a":"é","z":1}', canonical_json_bytes({"z": 1, "a": "é"}))
```

The test class uses `tempfile.TemporaryDirectory()` in `setUp`/`tearDown` and asserts all generated directories named in spec Section 6 exist.

- [ ] **Step 2: Run the lifecycle tests and confirm red**

Run: `python3.11 -m unittest tests.test_manifest -v`

Expected: exit `1` with `ModuleNotFoundError: No module named 'comic_sol'`.

- [ ] **Step 3: Implement the smallest deterministic lifecycle CLI**

Use `argparse`, `pathlib`, `json`, `hashlib`, `datetime`, `os`, `re`, `shutil`, and `tempfile`. Atomic writes create a sibling `.tmp`, flush, `os.fsync`, then `os.replace`; they do not delete unrelated interrupted temporary files. Events are one canonical compact JSON object plus newline and contain only event, UTC time, relative paths/hashes/counts/sanitized categories. `doctor` checks Python `>=3.11,<3.12`, exact Pillow `11.3.0`, font load at 42 px, templates, and output-root writability, and prints that agent capability detection remains pending.

- [ ] **Step 4: Verify lifecycle and doctor behavior**

Run: `python3.11 -m unittest tests.test_manifest tests.test_validation.TemplateContractTests -v && python3.11 scripts/comic_sol.py doctor --output-root /tmp/comic-sol-doctor`

Expected: all listed tests report `OK`; doctor exits `0` and prints PASS lines for Python, Pillow, font, templates, output root, plus `INFO image capability: inspect in agent session`.

- [ ] **Step 5: Commit lifecycle behavior**

```bash
git add scripts/comic_sol.py tests/test_manifest.py tests/test_validation.py
git commit -m "feat: initialize and track Comic Sol projects"
```

### Task T03: Implement strict validation and five fixed layouts

**Files:**

- Create: `scripts/validate_project.py`
- Modify: `scripts/comic_sol.py`
- Modify: `tests/test_validation.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class ValidationIssue:
    path: str
    field: str
    message: str

class ProjectValidationError(ValueError):
    issues: tuple[ValidationIssue, ...]

def validate_manifest(data: dict[str, object]) -> list[ValidationIssue]: ...
def validate_character_bible(data: dict[str, object]) -> list[ValidationIssue]: ...
def validate_story_plan(data: dict[str, object]) -> list[ValidationIssue]: ...
def validate_storyboard(data: dict[str, object], story: dict[str, object],
                        characters: dict[str, object]) -> list[ValidationIssue]: ...
def validate_panel_record(data: dict[str, object]) -> list[ValidationIssue]: ...
def validate_project(project_dir: Path, stage: str = "all") -> list[ValidationIssue]: ...
def main(argv: list[str] | None = None) -> int: ...
```

CLI: `validate_project.py PROJECT_DIR [--stage all|plan|storyboard|panels|final] [--json]`. Exit `0` means valid; exit `2` means validation issues; exit `1` means invocation/I/O failure.

- [ ] **Step 1: Write failing schema, limits, layout, and cross-reference tests**

Append concrete tests that load valid fixture dictionaries from templates and mutate one property per subtest. Required assertions cover unknown fields, bad ID, 1–4 pages, 12 panels, 4 panels/page, 2–5 scenes, 2–5 character invariants, valid scene/character/speaker references, 0–3 text items, dialogue 32/caption 45/SFX 3/item and 45/panel word limits, eight anchors, normalized tail coordinates, seven exact QA checks, paths relative to project, lowercase 64-hex hashes, page bounds and rectangle overlap. Add this geometry assertion:

```python
def test_all_layouts_use_exact_page_geometry(self):
    expected_counts = {
        "full-page": 1,
        "two-horizontal": 2,
        "three-horizontal": 3,
        "hero-top-two-bottom": 3,
        "two-top-hero-bottom": 3,
    }
    for name, count in expected_counts.items():
        rects = layout_rects(name)
        self.assertEqual(count, len(rects))
        for rect in rects:
            self.assertGreaterEqual(rect["x"], 64)
            self.assertGreaterEqual(rect["y"], 64)
            self.assertLessEqual(rect["x"] + rect["width"], 1536)
            self.assertLessEqual(rect["y"] + rect["height"], 2336)
        self.assertFalse(any(rectangles_overlap(a, b) for i, a in enumerate(rects) for b in rects[i + 1:]))
```

- [ ] **Step 2: Run strict validation tests and confirm red**

Run: `python3.11 -m unittest tests.test_validation -v`

Expected: exit `1` because `validate_project`, `rectangles_overlap`, or strict validation behavior is absent.

- [ ] **Step 3: Implement explicit allow-list validators**

Implement field allow-lists and type/range checks directly; do not add a JSON Schema dependency. Generate preset rectangles solely from constants `PAGE_WIDTH=1600`, `PAGE_HEIGHT=2400`, `MARGIN=64`, `GUTTER=32`. Sort issues by `(path, field, message)` for deterministic CLI output. `validate_project` reads only the files required by `stage`, validates hashes/images at `panels`/`final`, confirms PNG/JPEG/WebP inputs are readable and at least 512 px with aspect tolerance ±2%, and uses Pillow to reject unintended alpha.

- [ ] **Step 4: Verify strict validation**

Run: `python3.11 -m unittest tests.test_validation -v`

Expected: every validation/layout test passes and the command ends with `OK`.

- [ ] **Step 5: Commit validation and layout geometry**

```bash
git add scripts/comic_sol.py scripts/validate_project.py tests/test_validation.py
git commit -m "feat: validate Comic Sol projects and layouts"
```

### Task T04: Implement cache keys, selective invalidation, retry accounting, and resume

**Files:**

- Modify: `scripts/comic_sol.py`
- Create: `tests/test_resume.py`
- Modify: `tests/test_manifest.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class ResumeAction:
    stage: str
    action: Literal["reuse", "regenerate", "rerun", "blocked"]
    artifact: str
    reason: str

def stage_cache_key(stage: str, canonical_inputs: list[object],
                    files: list[Path], stage_version: str) -> str: ...
def build_resume_plan(project_dir: Path) -> list[ResumeAction]: ...
def invalidate_from(project_dir: Path, stage: str) -> list[str]: ...
def record_generation_attempt(project_dir: Path, panel_id: str,
                              kind: Literal["initial", "visual_retry", "transient_repeat"],
                              attempt_path: Path) -> dict[str, int]: ...
def promote_attempt(project_dir: Path, panel_id: str,
                    attempt_path: Path) -> Path: ...
def record_override(project_dir: Path, panel_id: str, reason: str) -> None: ...
```

Extend CLI with `resume-plan PROJECT_DIR [--json]`, `invalidate PROJECT_DIR STAGE`, `record-attempt PROJECT_DIR PANEL_ID KIND PATH`, `promote-attempt PROJECT_DIR PANEL_ID PATH`, and `override-panel PROJECT_DIR PANEL_ID --reason TEXT`.

- [ ] **Step 1: Write failing resume and budget tests**

Create tests for: identical completed project returns all `reuse` and does not change any file mtime/hash; dialogue-only storyboard change reruns `lettering` onward while raw/clean hashes remain; fingerprint/reference change regenerates dependent panels onward; missing/hash-mismatched artifact invalidates earliest owner stage; interrupted `.tmp` is reported but not deleted; attempt `n` is retained before accepted promotion; third visual retry is rejected; ninth extra call is rejected; transient repeats consume global but not per-panel visual budget; corrupt images and safety refusals cannot be overridden. Include:

```python
def test_noop_resume_does_not_write_any_file(self):
    before = {p.relative_to(self.project): (p.stat().st_mtime_ns, sha256_file(p))
              for p in self.project.rglob("*") if p.is_file()}
    actions = build_resume_plan(self.project)
    after = {p.relative_to(self.project): (p.stat().st_mtime_ns, sha256_file(p))
             for p in self.project.rglob("*") if p.is_file()}
    self.assertTrue(actions)
    self.assertTrue(all(action.action == "reuse" for action in actions))
    self.assertEqual(before, after)
```

- [ ] **Step 2: Run resume tests and confirm red**

Run: `python3.11 -m unittest tests.test_resume -v`

Expected: exit `1` with missing resume/retry interfaces.

- [ ] **Step 3: Implement stage dependency and budget tables**

Use the exact ordered stages from the manifest. Cache keys hash canonical JSON inputs, direct file hashes, and stage version, excluding timestamps. Add normative `cache_keys`, `generation_counters`, and per-panel dependency-hash fields to `references/schemas.md` and `templates/manifest.json`, rejecting unknown counter/cache keys. Invalidation removes artifact entries from the manifest but never deletes editable files automatically. Promotion verifies the raster, moves the previous accepted image to `.attempt-{attempt_number}.png` when necessary, and atomically replaces only the target panel. A no-op resume performs reads only, including no event append.

- [ ] **Step 4: Verify resume, retry, and prior lifecycle behavior**

Run: `python3.11 -m unittest tests.test_resume tests.test_manifest -v`

Expected: all resume, budget, transition, and initialization tests pass with `OK`.

- [ ] **Step 5: Commit resumability**

```bash
git add scripts/comic_sol.py references/schemas.md templates/manifest.json tests/test_resume.py tests/test_manifest.py
git commit -m "feat: resume and selectively repair comic projects"
```

### Task T05: Implement deterministic normalization and lettering

**Files:**

- Create: `scripts/lettering.py`
- Create: `tests/test_lettering.py`

**Interfaces:**

```python
class LetteringError(ValueError):
    item_id: str

@dataclass(frozen=True)
class PlacedText:
    item_id: str
    box: tuple[int, int, int, int]
    font_size: int
    lines: tuple[str, ...]
    anchor: str

def normalize_panel(source: Path, destination: Path,
                    target_width: int, target_height: int) -> None: ...
def sanitize_text(kind: str, content: str) -> str: ...
def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont,
              max_width: int) -> tuple[str, ...]: ...
def place_text_items(image_size: tuple[int, int], items: list[dict[str, object]],
                     font_path: Path) -> list[PlacedText]: ...
def letter_panel(clean_path: Path, output_path: Path,
                 text_items: list[dict[str, object]], font_path: Path) -> list[PlacedText]: ...
def letter_project(project_dir: Path, panel_ids: list[str] | None = None) -> list[Path]: ...
def main(argv: list[str] | None = None) -> int: ...
```

CLI: `lettering.py PROJECT_DIR [--panel PANEL_ID]`; exit `2` for item-specific overflow/glyph/content errors.

- [ ] **Step 1: Write failing lettering tests**

Tests cover EXIF transpose, RGB conversion, exact center crop, NFC normalization, control rejection, word limits, straight-quote preservation, unsupported glyph names, greedy pixel wrapping, explicit paragraph breaks, priority/ID order, eight-anchor clockwise search, 42→24 px steps, SFX 64→24 px steps, 16 px stacking gap, no overlap, dialogue ellipse/4 px outline/24 px padding/tail, caption rectangle/4 px outline/20 px padding, SFX 6 px white plus 3 px black strokes, stable pixel digest, and item-specific overflow. Include:

```python
def test_overflow_names_item_and_never_writes_partial_output(self):
    output = self.root / "lettered.png"
    item = {"id": "p01-01-t01", "kind": "caption", "speaker": None,
            "content": "wide " * 45, "anchor": "top-left",
            "tail_target": None, "priority": 1}
    with self.assertRaisesRegex(LetteringError, "p01-01-t01"):
        letter_panel(self.clean, output, [item], FONT)
    self.assertFalse(output.exists())
```

- [ ] **Step 2: Run lettering tests and confirm red**

Run: `python3.11 -m unittest tests.test_lettering -v`

Expected: exit `1` with `ModuleNotFoundError: No module named 'lettering'`.

- [ ] **Step 3: Implement measured placement and drawing**

Use `ImageOps.exif_transpose`, RGB conversion, aspect-preserving LANCZOS resize and centered crop. Candidate zones are 42% × 30%, inset 4%; anchor order is top-left → top-center → top-right → middle-right → bottom-right → bottom-center → bottom-left → middle-left. Use `draw.textbbox` for wrapping/fitting. Check every glyph against the bundled font before drawing. Render to an in-memory copy and atomically save only after all items fit. Tail target is normalized `[x,y]`; draw its triangle before the dialogue ellipse so the shared edge is hidden.

- [ ] **Step 4: Verify lettering**

Run: `python3.11 -m unittest tests.test_lettering -v`

Expected: all sanitation, geometry, drawing, digest, and failure tests pass with `OK`.

- [ ] **Step 5: Commit lettering**

```bash
git add scripts/lettering.py tests/test_lettering.py
git commit -m "feat: letter comic panels deterministically"
```

### Task T06: Implement deterministic page composition

**Files:**

- Create: `scripts/compose.py`
- Create: `tests/test_compose.py`

**Interfaces:**

```python
class CompositionError(ValueError): ...
def compose_page(page: dict[str, object], project_dir: Path,
                 output_path: Path) -> Path: ...
def compose_project(project_dir: Path) -> list[Path]: ...
def main(argv: list[str] | None = None) -> int: ...
```

CLI: `compose.py PROJECT_DIR`; it refuses incomplete/error-level panels and writes `pages/page-001.png` onward.

- [ ] **Step 1: Write failing composition tests**

Use synthetic solid-red/green/blue lettered panels. Assert an opaque RGB 1600 × 2400 white canvas, storyboard order independent of directory order, exact rect placement, LANCZOS resizing, inward 6 px black border, 64 px margins/32 px gutters, `page-001.png` naming, metadata omission, stable decoded pixel digest, and no output for a missing/unaccepted panel.

```python
def test_missing_panel_prevents_partial_page(self):
    output = self.project / "pages/page-001.png"
    (self.project / "panels/lettered/p01-02.png").unlink()
    with self.assertRaisesRegex(CompositionError, "p01-02"):
        compose_project(self.project)
    self.assertFalse(output.exists())
```

- [ ] **Step 2: Run composition tests and confirm red**

Run: `python3.11 -m unittest tests.test_compose -v`

Expected: exit `1` with missing `compose` module/interface.

- [ ] **Step 3: Implement composition from validated storyboard rectangles**

Call `validate_project(..., stage="panels")` before drawing. Load only `panels/lettered/{panel_id}.png`, convert RGB, resize LANCZOS, paste at exact `rect`, and use `ImageDraw.rectangle(..., width=6)` within the rectangle. Render each page to memory/temporary path; publish pages only after every page composes successfully.

- [ ] **Step 4: Verify composition**

Run: `python3.11 -m unittest tests.test_compose -v`

Expected: all composition and error tests pass with `OK`.

- [ ] **Step 5: Commit page composition**

```bash
git add scripts/compose.py tests/test_compose.py
git commit -m "feat: compose deterministic comic pages"
```

### Task T07: Implement ordered raster PDF export

**Files:**

- Create: `scripts/export_pdf.py`
- Create: `tests/test_export_pdf.py`

**Interfaces:**

```python
class PdfExportError(ValueError): ...
def discover_pages(project_dir: Path) -> list[Path]: ...
def export_pdf(project_dir: Path, output_path: Path | None = None) -> Path: ...
def main(argv: list[str] | None = None) -> int: ...
```

CLI: `export_pdf.py PROJECT_DIR [--output PATH]`; default is `exports/{project_id}.pdf` where `project_id` comes from the validated manifest.

- [ ] **Step 1: Write failing PDF tests**

Generate three synthetic RGB pages with distinct corner pixels and intentionally shuffled creation order. Assert numeric filename ordering, exact page count, RGB mode, 1600 × 2400 size, 150 DPI metadata (within Pillow round-trip tolerance), no extra margin, custom/default output paths, atomic publication, and refusal of missing/non-contiguous/wrong-size pages.

```python
def test_pdf_uses_numeric_page_order(self):
    output = export_pdf(self.project)
    with Image.open(output) as pdf:
        colors = []
        for frame in range(pdf.n_frames):
            pdf.seek(frame)
            colors.append(pdf.convert("RGB").getpixel((100, 100)))
    self.assertEqual([self.red, self.green, self.blue], colors)
```

- [ ] **Step 2: Run PDF tests and confirm red**

Run: `python3.11 -m unittest tests.test_export_pdf -v`

Expected: exit `1` with missing `export_pdf` module/interface.

- [ ] **Step 3: Implement strict discovery and Pillow PDF save**

Match only `page-[0-9]{3}.png`, sort numerically, require pages `1..manifest.page_count`, open/verify every page before saving, convert to RGB, and call Pillow’s PDF writer with `resolution=150.0`, `save_all=True`, and ordered append images. Save to a sibling temporary PDF, reopen it to verify frames/order/size, then atomically replace the destination.

- [ ] **Step 4: Verify PDF export**

Run: `python3.11 -m unittest tests.test_export_pdf -v`

Expected: all PDF tests pass with `OK`.

- [ ] **Step 5: Commit export**

```bash
git add scripts/export_pdf.py tests/test_export_pdf.py
git commit -m "feat: export ordered comic PDF"
```

### Task T08: Implement human-readable QA report rendering

**Files:**

- Create: `scripts/render_report.py`
- Create: `tests/test_report.py`
- Modify: `templates/qa-report.md.tmpl`
- Modify: `references/schemas.md`

**Interfaces:**

```python
@dataclass(frozen=True)
class QaSummary:
    pages: int
    panels: int
    generation_attempts: int
    regenerated_panels: int
    accepted_warnings: int
    hard_failures: int

def summarize_qa(manifest: dict[str, object],
                 panel_records: list[dict[str, object]]) -> QaSummary: ...
def render_report(project_dir: Path, output_path: Path | None = None) -> Path: ...
def main(argv: list[str] | None = None) -> int: ...
```

CLI: `render_report.py PROJECT_DIR [--output PATH]`; default output is `qa/report.md`.

- [ ] **Step 1: Write failing report tests**

Create panel records covering pass, warning, retry, user override, and hard blocking failure. Assert all seven report sections, exact aggregates, seven-check table results, unresolved user impact, capability/reference support and degraded-mode disclosure, external-provider privacy disclosure, artifact-integrity results, PDF readability, and reused/regenerated resume summary.

```python
def test_report_distinguishes_all_decisions_and_has_no_template_tokens(self):
    output = render_report(self.project)
    text = output.read_text("utf-8")
    for phrase in ("Project summary", "Capability", "Panel QA", "Unresolved warnings",
                   "Artifact integrity", "Resume summary", "accept_with_warnings",
                   "regenerate", "override", "BLOCKED"):
        self.assertIn(phrase, text)
    self.assertNotIn("{{", text)
```

- [ ] **Step 2: Run report tests and confirm red**

Run: `python3.11 -m unittest tests.test_report -v`

Expected: exit `1` with missing `render_report` module/interface.

- [ ] **Step 3: Implement deterministic aggregation and token replacement**

Sort records by panel ID; escape Markdown table pipes/newlines in evidence; calculate counts from records rather than trusting manifest summaries; label absent warnings as `No unresolved warnings.`; list relative paths/hashes/dimensions/page/PDF checks; disclose whether references are unsupported and that provider policies govern transmitted prompts/references. Fail if any template token remains, then atomically write UTF-8 Markdown with one newline.

- [ ] **Step 4: Verify report rendering**

Run: `python3.11 -m unittest tests.test_report -v`

Expected: all aggregation, disclosure, integrity, and decision tests pass with `OK`.

- [ ] **Step 5: Commit QA reporting**

```bash
git add scripts/render_report.py templates/qa-report.md.tmpl references/schemas.md tests/test_report.py
git commit -m "feat: render transparent comic QA reports"
```

### Task T09: Author the installable skill and progressive agent workflow

**Files:**

- Create: `SKILL.md`
- Create: `references/workflow.md`
- Create: `references/creative-direction.md`
- Create: `references/capability-detection.md`
- Create: `references/visual-qa.md`
- Create: `references/safety-ip.md`
- Modify: `tests/test_validation.py`

**Interfaces:**

- `SKILL.md` frontmatter has exactly `name` and `description`; name is `comic-sol`; description includes create/storyboard/render/resume/export intent and prompt/story/`.txt`/`.md` inputs.
- The body routes agent work to the six references and exact T02–T08 CLI commands.
- Workflow input detection order is `resume` precedence, existing `.txt`/`.md`, pasted prose (`>=120` characters or two paragraph breaks), then short prompt; rejects missing/invalid UTF-8/>200 KiB source before initialization.
- The agent writes prompts in exact order: style anchor, scene anchor, exact character fingerprints, action/expression, camera/composition/lighting, text-safe areas, negatives.
- Capability preference is references → dimensions/aspect → direct PNG; compatible output is local raster, both dimensions at least 512; feature flags only are recorded.
- Visual QA requires exactly seven checks and one correction clause per retry; failed attempts are retained and passing panels are untouched.

- [ ] **Step 1: Write failing static skill contract tests**

Append tests that parse frontmatter without PyYAML, assert only two keys, assert every reference link resolves, reject provider SDK/API-key phrases in scripts and capability reference, verify the exact unavailable-capability leading error, all four material-question conditions, defaults, state order, seven checks, retry caps, completion response paths/status, and deterministic CLI command names. Include:

```python
def test_skill_is_trigger_focused_and_all_progressive_links_exist(self):
    text = (ROOT / "SKILL.md").read_text("utf-8")
    frontmatter = text.split("---", 2)[1]
    keys = [line.split(":", 1)[0] for line in frontmatter.splitlines() if ":" in line]
    self.assertEqual(["name", "description"], keys)
    for name in ("workflow", "creative-direction", "capability-detection",
                 "visual-qa", "safety-ip", "schemas"):
        self.assertIn(f"references/{name}.md", text)
        self.assertTrue((ROOT / "references" / f"{name}.md").is_file())
```

- [ ] **Step 2: Run skill contract tests and confirm red**

Run: `python3.11 -m unittest tests.test_validation -v`

Expected: exit `1` because `SKILL.md` and five agent references do not yet exist.

- [ ] **Step 3: Write concise orchestration and progressive references**

Keep `SKILL.md` below 220 lines and place normative detail in references. `workflow.md` covers all ten stages, generated directory boundary, materially missing questions, defaults, status transitions, exact CLI invocations, completion paths, and failure taxonomy. `creative-direction.md` covers original direction, 2–5 scenes, fingerprints/invariants, canonical references, scene-reference threshold, panel scripting, layouts, and prompt construction. `capability-detection.md` contains the exact error from spec Section 10 and prohibits secrets/provider imports. `visual-qa.md` defines seven checks, evidence, decisions, retry/override/call budgets, transient repeat, composed-page QA, and blocked export. `safety-ip.md` covers local artifacts, prompt minimization, secret warning, sanitized logs, external policy disclosure, style translation, real people, minors, refusal, and no evasion.

- [ ] **Step 4: Verify the skill contract and deterministic suite**

Run: `python3.11 -m unittest tests.test_validation -v && ! rg -n '(OPENAI_API_KEY|ANTHROPIC_API_KEY|api[_ -]?key\s*=|requests\.|httpx\.|urllib\.request)' scripts references/capability-detection.md`

Expected: validation tests report `OK`; `rg` prints nothing and the negated scan exits `0`.

- [ ] **Step 5: Commit the agent-facing product**

```bash
git add SKILL.md references tests/test_validation.py
git commit -m "feat: orchestrate comics as an installable skill"
```

### Task T10: Add offline end-to-end fixtures and full deterministic integration tests

**Files:**

- Create: `tests/fixtures/valid-one-page/` and its complete generated-project tree
- Create: `tests/fixtures/interrupted-two-page/` and its partial generated-project tree
- Create: `tests/fixtures/demo-story.md`
- Modify: `tests/test_resume.py`
- Modify: `tests/test_report.py`
- Modify: `tests/test_validation.py`
- Modify: `tests/test_lettering.py`
- Modify: `tests/test_compose.py`
- Modify: `tests/test_export_pdf.py`

**Interfaces:**

- Valid fixture contains 1 page, 3 synthetic panels, canonical character reference, prompts, seven-check QA records, and complete semantic files; it is copied to a temp directory before mutation.
- Interrupted fixture contains 2 pages, one accepted panel, one preserved failed attempt, no downstream pages/PDF, and expected resume actions in test assertions.
- Integration path calls Python functions in order: `validate_project → letter_project → compose_project → export_pdf → render_report → transition`.

- [ ] **Step 1: Write failing integration tests before completing fixture trees**

```python
def test_valid_fixture_runs_deterministic_pipeline(self):
    self.assertEqual([], validate_project(self.project, "panels"))
    lettered = letter_project(self.project)
    pages = compose_project(self.project)
    pdf = export_pdf(self.project)
    report = render_report(self.project)
    self.assertEqual(3, len(lettered))
    self.assertEqual(["page-001.png"], [p.name for p in pages])
    with Image.open(pdf) as document:
        self.assertEqual(1, document.n_frames)
    self.assertIn("No unresolved warnings", report.read_text("utf-8"))

def test_interrupted_fixture_reuses_pass_and_regenerates_only_failure(self):
    actions = build_resume_plan(self.project)
    panel_actions = {a.artifact: a.action for a in actions if a.artifact.startswith("p")}
    self.assertEqual("reuse", panel_actions["p01-01"])
    self.assertEqual("regenerate", panel_actions["p01-02"])
```

- [ ] **Step 2: Run the full suite and confirm the fixture red state**

Run: `python3.11 -m unittest discover -s tests -v`

Expected: exit `1`; unit tests remain green but new integration tests fail on absent/incomplete fixtures.

- [ ] **Step 3: Build fixtures only from synthetic deterministic pixels**

Create 512+ px solid/gradient geometric PNGs with Pillow, no image model and no copyrighted art. Populate every JSON/hash through production canonical writers, then commit the results. Add `tests/fixtures/demo-story.md` as a complete original 150–250 word UTF-8 story used for the live source-file case. Ensure the valid fixture reaches `QA_READY` before integration runs downstream; ensure the interrupted fixture’s accepted panel hash remains unchanged after resume planning. Do not commit temp files or machine-specific absolute paths.

- [ ] **Step 4: Run the authoritative offline gate**

Run: `python3.11 -m unittest discover -s tests -v`

Expected: exit `0`, every discovered test passes, final line `OK`, and no test performs a network/image API call.

- [ ] **Step 5: Commit offline integration evidence**

```bash
git add tests/fixtures tests
git commit -m "test: cover the offline Comic Sol pipeline"
```

### Task T11: Complete packaging, installation, support, and Build Week evidence

**Files:**

- Create: `LICENSE`
- Modify: `README.md`
- Modify: `assets/README.md`
- Modify: `tests/test_validation.py`

**Interfaces:**

- README documents clone/copy-to-skills installation, Python 3.11, `Pillow==11.3.0`, test/doctor commands, one natural-language invocation, output tree, architecture, capability requirements/error, support matrix, privacy/IP/limitations, clean-room test, sample-output inspection, demo steps, Codex/GPT-5.6 Sol collaboration, public-repo checklist, and `/feedback` Session ID procedure.
- The `/feedback` ID is inserted only after the real session command returns it; until then README describes the exact pre-submission procedure without an invented value.
- LICENSE is a complete OSI-compatible license chosen for the original project; third-party font licensing remains separately documented.

- [ ] **Step 1: Write failing package/documentation checks**

Append a `PackagingTests` class that checks required files, README commands/language, no build/server steps, exact dependency pin, output artifacts, supported platforms, capability error link, limitations, demo duration, public-repo check, Build Week cutoff/evidence, and `/feedback` procedure. Check `LICENSE` is non-empty and Noto licensing remains distinct.

```python
def test_readme_is_judge_runnable_without_a_build_service(self):
    readme = (ROOT / "README.md").read_text("utf-8")
    for required in ("Pillow==11.3.0", "python3.11 -m unittest discover -s tests -v",
                     "python3.11 scripts/comic_sol.py doctor", "one natural-language",
                     "/feedback", "under three minutes", "GPT-5.6 Sol"):
        self.assertIn(required, readme)
    self.assertNotRegex(readme.lower(), r"npm run|start the server|docker compose")
```

- [ ] **Step 2: Run packaging checks and confirm red**

Run: `python3.11 -m unittest tests.test_validation.PackagingTests -v`

Expected: exit `1` until LICENSE and all required README sections are present.

- [ ] **Step 3: Write judge-facing documentation and evidence checklist**

Preserve any useful existing README content while reorganizing it around install → invoke → inspect → test → support. Document verified Codex paths from current official docs at implementation time, plus a host-agnostic copy method. Add commands for a fresh virtual environment and Windows equivalents. Link committed synthetic/sample output paths rather than embedding unverified remote URLs. Record that real generated prompts/references go through the selected external tool’s policies. Add a pre-submission checklist to make the repository public, verify logged out, run clean-room install on Windows/Linux, insert the real `/feedback` Session ID, and confirm all work dates after July 13, 2026.

- [ ] **Step 4: Verify package and clean-room behavior**

Run:

```bash
python3.11 -m unittest discover -s tests -v
tmp_dir=$(mktemp -d)
python3.11 -m venv "$tmp_dir/venv"
"$tmp_dir/venv/bin/python" -m pip install Pillow==11.3.0
"$tmp_dir/venv/bin/python" scripts/comic_sol.py doctor --output-root "$tmp_dir/output"
```

Expected: suite exits `0` with `OK`; Pillow installation succeeds; doctor exits `0` with all deterministic checks PASS and image capability marked for agent-session inspection.

- [ ] **Step 5: Commit packaging and evidence docs**

```bash
git add LICENSE README.md assets/README.md tests/test_validation.py
git commit -m "docs: package Comic Sol for Build Week"
```

### Task T12: Run live agent acceptance, failure-path rehearsal, and final release gate

**Files:**

- Modify only if evidence is real and available: `README.md`
- Create only from the live accepted run: `samples/sunlight-courier/` containing the reviewed manifest, story/character/storyboard plans, references, prompts, accepted panel variants, panel QA, page PNGs, PDF, event log, and QA report
- Modify: `tests/test_validation.py` only if a deterministic regression is discovered
- Modify the responsible production/test file only when a live run exposes a reproducible defect; use a separate red/green fix commit before continuing this task

**Interfaces:**

- Live invocation A: `Make a 2-page manga about a courier delivering sunlight to an underground city.`
- Live invocation B: `Turn tests/fixtures/demo-story.md into a short anime comic.`
- Disabled-capability invocation must preserve planning artifacts and emit the exact Section 10 leading error followed by the absolute project path.
- Demo evidence records page/panel/retry counts, artifacts, under-three-minute timing, no-op resume, and real `/feedback` Codex Session ID.

- [ ] **Step 1: Establish the pre-live green baseline**

Run: `python3.11 -m unittest discover -s tests -v && python3.11 scripts/comic_sol.py doctor`

Expected: tests exit `0` with `OK`; doctor exits `0`; only image capability is explicitly deferred to the live agent session.

- [ ] **Step 2: Execute the two happy paths through natural language**

In a clean Codex session with GPT-5.6 Sol and an exposed image-generation capability, issue invocation A without manual script commands. Confirm it asks no question, announces defaults, creates canonical references, saves prompts and editable semantic files, writes all panel QA records, selectively regenerates only a deliberately rejected panel if a natural error occurs, letters/composes/exports, and reports clickable manifest/pages/PDF/QA paths. Repeat with invocation B to prove `.md` mode. Record actual commands/session evidence in README only after both runs finish.

Expected: both projects end `COMPLETE` or `COMPLETE_WITH_WARNINGS`, never `BLOCKED`; all acceptance artifacts exist and validate.

- [ ] **Step 3: Execute unavailable-capability and no-op resume paths**

In a session without image generation, invoke the same request. Confirm status `BLOCKED`, planning artifacts retained, no empty panel files, and exact leading error. Re-enable capability and say `resume this Comic Sol project`; confirm completion. Invoke resume again and compare recursive file hashes/mtimes captured before and after.

Expected: blocked/resume works; second resume reports full reuse and changes no artifact, timestamp, or event log.

- [ ] **Step 4: Run the release verification gate**

Run:

```bash
python3.11 -m unittest discover -s tests -v
python3.11 scripts/validate_project.py comic-sol-output/sunlight-courier --stage final
python3.11 scripts/comic_sol.py resume-plan comic-sol-output/sunlight-courier --json
git diff --check
git status --short
```

Expected: tests and final validation exit `0`; resume plan contains only `reuse`; diff check is clean; status lists only intentional sample/README evidence changes. Then rehearse the Section 16 timeline with a stopwatch; expected elapsed time is less than `00:03:00`.

- [ ] **Step 5: Capture the real feedback identifier and commit release evidence**

Run `/feedback` in the Codex session, copy the returned real Session ID into the README submission section, re-run the packaging test and full suite, then commit only verified evidence:

```bash
python3.11 -m unittest tests.test_validation.PackagingTests -v
python3.11 -m unittest discover -s tests -v
git add README.md tests/test_validation.py
git add samples/sunlight-courier
git commit -m "test: verify Comic Sol end to end"
```

Expected: both suites exit `0` with `OK`; commit contains no secrets, absolute paths, provider raw responses, or unreviewed failed images.

## 4. Verification gating summary

No task advances on prose review alone. The required gate is the command below plus inspection of its stated expected result.

| Task | Required proof before commit |
|---|---|
| T01 | `python3.11 -m unittest tests.test_validation.TemplateContractTests -v` → `Ran 1 test`, `OK` |
| T02 | lifecycle suite + `comic_sol.py doctor` → tests `OK`, doctor exit `0` |
| T03 | `python3.11 -m unittest tests.test_validation -v` → `OK` |
| T04 | manifest/resume suites → `OK`, no-op file map identical |
| T05 | `python3.11 -m unittest tests.test_lettering -v` → `OK` |
| T06 | `python3.11 -m unittest tests.test_compose -v` → `OK` |
| T07 | `python3.11 -m unittest tests.test_export_pdf -v` → `OK` |
| T08 | `python3.11 -m unittest tests.test_report -v` → `OK` |
| T09 | validation suite `OK` plus provider/secret/network scan prints nothing |
| T10 | full offline discovery → exit `0`, `OK` |
| T11 | full suite + clean virtual-environment doctor → both exit `0` |
| T12 | full suite, live final validation, all-reuse plan, clean diff, timed demo `<03:00` |

At every task boundary also run `git diff --check` and `git status --short`; do not stage unrelated user changes. T10 onward uses the full offline suite as a regression gate. A live failure in T12 returns to the responsible task’s focused test: reproduce red offline, implement the smallest correction, run focused green, then run the entire suite.

## 5. Acceptance criteria traceability

| AC | Requirement | Implemented by | Proved by |
|---:|---|---|---|
| 1 | Installable skill triggers from one natural-language request | T09, T11, T12 | Static frontmatter/link test; live invocation A |
| 2 | Short prompt, pasted story, `.txt`, `.md`, resume detection | T09, T10, T12 | Workflow contract assertions; short/Markdown live runs; resume run |
| 3 | Safe default completes without questions | T09, T12 | Material-question/default static tests; invocation A observation |
| 4 | Complete editable project artifact set | T01–T10, T12 | Valid fixture integration; live final project validation |
| 5 | 1–4 pages, ≤12 panels, ≤4/page, five layouts | T03, T09 | Strict limit and exact-geometry tests |
| 6 | Canonical recurring-character reference, 2–5 invariants, exact fingerprint reuse | T03, T09, T12 | Schema/prompt contract tests; live prompt/reference inspection |
| 7 | Feature-recorded capability, no provider secrets/API | T09, T11 | Static capability fields and forbidden-import/secret scan |
| 8 | Unavailable capability blocks and preserves plans with exact error | T02, T04, T09, T12 | Static exact-message test; disabled-capability live run |
| 9 | Seven panel QA checks | T01, T03, T08, T09 | Panel-record validator and report table tests |
| 10 | Only failed panel regenerates; prior attempt retained; passing hashes stable | T04, T09, T10, T12 | Interrupted fixture and selective resume hash assertions |
| 11 | 2/panel and 8 global caps; unresolved errors excluded unless allowed override | T04, T06, T09 | Budget/override tests and compose precondition test |
| 12 | No generated dialogue; deterministic dialogue/caption/SFX | T05, T09 | Prompt negative contract; lettering pixel/shape tests |
| 13 | No silent clipping; overflow/glyph error names item | T05 | Item-specific overflow and unsupported-glyph tests |
| 14 | RGB 1600 × 2400 ordered bordered PNGs; matching readable PDF | T06, T07, T10 | Composition/PDF focused and integration tests |
| 15 | No-change resume writes nothing; dialogue change invalidates downstream only | T04, T10, T12 | Mtime/hash map test, invalidation test, live no-op resume |
| 16 | Every deterministic script has offline `unittest` coverage | T02–T10 | `unittest discover` exits `0` |
| 17 | Report distinguishes pass/warning/retry/override/block and user impact | T08, T10 | Decision matrix/report integration tests |
| 18 | Originality, privacy, refusal, logging and provider disclosures | T08, T09, T11 | Static reference/report tests and forbidden-content scan |
| 19 | Public repo installs/tests without build service; samples immediately inspectable | T11, T12 | Clean-room doctor/test, logged-out checklist, committed samples |
| 20 | Demo covers full workflow and resume under three minutes | T11, T12 | Stopwatch rehearsal and documented demo evidence |

Coverage is 20/20; no criterion depends solely on an unverified documentation claim.

## 6. Specification-section coverage

| Spec section | Task coverage |
|---|---|
| 1 Product thesis/target user | T09 skill UX; T11 judge-facing README; T12 live proof |
| 2 Product principles | T02–T10 artifact/determinism/resume; T09 originality/orchestration; T08 honest QA |
| 3 Goals/non-goals | T01–T12 must-have; global constraints/cut list prevent scope expansion |
| 4 Considered approaches | Header architecture and T09 preserve selected agent-orchestrated artifact-first approach |
| 5 Selected architecture/state machine | T02 lifecycle; T03 gates; T09 agent/deterministic boundary |
| 6 Package/components | Fixed inventory; T01–T11 create every path |
| 7 Invocation UX/modes | T02 initialization; T09 workflow; T12 live acceptance |
| 8 Schemas | T01 contracts; T03 validators; T08 report projection |
| 9 Pipeline/data flow | T02–T08 deterministic stages; T09 ten-stage orchestration; T10 integration |
| 10 Capability detection | T09 detection/error; T12 available/unavailable runs |
| 11 Consistency/layout/text/export | T03 layouts; T05 lettering; T06 compose; T07 export; T09 anchors |
| 12 Resume/cache/retry/failures | T02 atomic writes; T04 cache/budgets/invalidation; T10 interrupted fixture |
| 13 Privacy/IP/safety | T08 disclosure; T09 safety reference; T11 README |
| 14 Testing | T01–T10 TDD and offline integration |
| 15 Packaging/install/support | T01 font provenance; T09 skill package; T11 clean-room docs |
| 16 Build Week/demo | T11 evidence/docs; T12 live/timed verification |
| 17 Acceptance criteria | Trace table above and T12 release gate |
| 18 Delivery tiers | Schedule and stretch gate below |
| 19 Scope resolution | Global constraints, fixed inventory, and explicit cut list below |

## 7. Three-day delivery schedule

### Day 1 — Skill contract and artifacts

| Sequence | Task | Target outcome |
|---:|---|---|
| 1 | T01 | Frozen schemas/templates/font license contract |
| 2 | T02 | Project init, state transitions, atomic I/O, doctor |
| 3 | T03 | Strict validators and five exact layouts |
| 4 | T04 | Cache keys, invalidation, retry accounting, resume |
| 5 | T09 first pass | `SKILL.md` plus workflow/schema/capability references aligned to stable CLIs |

Day 1 exit gate: T01–T04 focused tests and T09 static contract pass; one fixture-like temporary project initializes, validates its planning files, and produces a deterministic resume plan.

### Day 2 — Visual pipeline and deterministic production

| Sequence | Task | Target outcome |
|---:|---|---|
| 1 | T05 | Normalized and deterministically lettered panels |
| 2 | T06 | Exact 1600 × 2400 composed pages |
| 3 | T07 | Ordered readable raster PDF |
| 4 | T08 | Transparent Markdown QA report |
| 5 | T09 final pass | Creative, QA, privacy/IP/safety agent procedures aligned to production behavior |

Day 2 exit gate: focused suites T05–T09 pass and a temporary synthetic project runs from accepted clean panels through lettered panels, page PNG, PDF, and QA report.

### Day 3 — Integration, evidence, and demo

| Sequence | Task | Target outcome |
|---:|---|---|
| 1 | T10 | Two offline fixtures and all deterministic tests green |
| 2 | T11 | Install/support/license/evidence docs and clean-room verification |
| 3 | T12 | Two live happy paths, unavailable/resume path, real samples/feedback ID, timed demo |

Day 3 exit gate: all 20 acceptance criteria have evidence, the full offline suite and final project validation pass, public clean-room installation is verified on Linux and Windows, and the rehearsed demo is under three minutes.

## 8. Stretch queue — locked until must-have passes

Eligibility requires T12’s complete release gate, 20/20 acceptance evidence, zero error-level QA issues, clean public install, and at least four hours remaining on Day 3. Stop stretch work immediately if it threatens demo rehearsal or release verification.

### S01: Right-to-left reading

Modify `scripts/comic_sol.py`, `scripts/validate_project.py`, `scripts/compose.py`, `references/workflow.md`, `references/schemas.md`, `tests/test_validation.py`, and `tests/test_compose.py`. Add failing tests proving reversed panel reading order and page order for the same five layouts, implement `reading_direction="rtl"`, run focused plus full suites, commit `feat: support right-to-left comic reading`.

### S02: CJK font option

Add a redistributable static CJK font under `assets/fonts/`, record its actual license/digest in `assets/README.md`, modify `scripts/lettering.py` and schema/workflow references, and add failing deterministic font-selection/glyph tests to `tests/test_lettering.py`. Proceed only if repository size remains acceptable. Commit `feat: add deterministic CJK lettering`.

### S03: Contact sheet

Add contact-sheet behavior to `scripts/compose.py` without a seventh production script. First add `tests/test_compose.py` assertions for labeled references/panels, ordering, RGB output, and fixed geometry; implement `compose.py contact-sheet PROJECT_DIR`; run full suite; commit `feat: add comic review contact sheet`.

### S04: Project overrides

Extend `scripts/comic_sol.py`, `scripts/validate_project.py`, workflow/schema references, and manifest/resume tests for a user-authored `project-overrides.json` limited to page count, palette, and typography. Prove overrides participate in cache keys and invalidation before implementation. Commit `feat: support comic project overrides`.

### S05: CBZ export

Extend `scripts/export_pdf.py` with `--format cbz`; add `tests/test_export_pdf.py` assertions for deterministic ZIP member order, page bytes, timestamps fixed to the ZIP epoch, and no extra files. Use stdlib `zipfile`, run full suite, commit `feat: export comic book archives`.

## 9. Explicit cut list

Do not add a web UI, frontend, server, dashboard, API service, database, auth, cloud state, queue, direct provider adapter, API-key setup, model training, freeform layout, drag-and-drop editor, vector/PSD/SVG/EPUB/CMYK/bleed pipeline, more than 4 pages/12 panels, multi-project character library, OCR, translation, full multilingual typography, computer-vision scoring, telemetry, analytics, billing, collaboration, or marketplace automation. A request for any cut item requires a new approved design specification; it cannot enter this plan as incidental work.

## 10. Final self-review checklist

Before declaring implementation complete, the executing agent must run and record all of the following:

- [ ] Every spec section 1–19 maps to at least one task in Section 6.
- [ ] Every fixed package path in spec Section 6 appears in Section 1 and a creation/modification task.
- [ ] Every task T01–T12 has a red test, exact green verification command, expected result, implementation boundary, and commit message.
- [ ] All Python signatures used by later tasks exactly match the producing task’s interface block.
- [ ] The full suite passes with `python3.11 -m unittest discover -s tests -v` and performs no network/image API call.
- [ ] Search plan and implementation for incomplete-work markers and remove them before release.
- [ ] Acceptance trace contains exactly 20 numbered rows and every row has task ownership plus proof.
- [ ] `git diff --check` succeeds; `git status --short` contains only intentional files.
- [ ] No deterministic script imports a model/provider/network SDK or reads a credential.
- [ ] T12 live evidence proves one-invocation happy path, selective panel repair, unavailable capability, downstream-only invalidation, no-op resume, final artifacts, and demo time under three minutes.
