# Speaker-Aware Balloon Tails Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers/subagent-driven-development (recommended) or superpowers/executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace ambiguous free-coordinate triangular balloon tails with validated speaker-aware semantics, deterministic organic geometry, hash-bound provenance, and fail-closed visual evidence.

**Architecture:** Storyboard validation owns semantic correctness; `letter_panels.py` resolves one canonical `TailGeometry` record and rasterizes its cubic silhouette into the existing supersampled balloon mask; lettering provenance binds that record; page quality cross-checks reviewer regions against current geometry. Legacy `tail_target` remains parseable but blocks lettering and later stages with `balloon-tail-migration-required`.

**Tech Stack:** Python 3.11+, Pillow, `unittest`, canonical JSON/SHA-256, existing transactional project I/O.

## Global Constraints

- Canonical engine remains `scripts/*.py`; runtime files changed here remain required wheel members.
- No new dependency, provider, network call, GUI, or MCP tool.
- Exact MCP surface remains 17 tools.
- New dialogue requires `speaker`, `voice_source`, and normalized `speaker_anchor`.
- `voice_source` is exactly `human` or `device`; device entities still resolve through the character bible and current panel.
- Captions and SFX have no dialogue-only fields or tail.
- Legacy `tail_target` is never silently reinterpreted and produces `balloon-tail-migration-required` at lettering and later stages.
- Deterministic mechanics evidence must not be presented as visual-quality proof.
- Existing `v2.0.0rc3` tag and artifacts remain immutable.

---

### Task 1: Storyboard semantics and migration boundary

**Files:**
- Modify: `scripts/validate_project.py:410-465`
- Modify: `scripts/letter_panels.py:675-805`
- Modify: `references/schemas.md:178-197`
- Modify: `references/workflow.md:77-83,136-142`
- Modify: `tests/test_validation.py`
- Modify: `tests/test_lettering.py`
- Modify: synthetic/committed storyboard fixtures that represent current valid projects

**Interfaces:**
- Consumes: text item dictionaries from `plan/storyboard.json`.
- Produces: validated fields `voice_source: Literal["human", "device"]` and `speaker_anchor: list[number, number]`; stable migration category `balloon-tail-migration-required`.

- [ ] **Step 1: Write RED schema tests**

Add tests proving: current dialogue accepts exactly the new fields; missing/invalid fields fail; legacy `tail_target` yields the migration category; caption/SFX reject all dialogue-only fields; a device speaker must resolve in the character bible and current panel.

- [ ] **Step 2: Verify RED**

Run: `/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest tests.test_validation tests.test_lettering -v`

Expected: failures because the validator only allows `tail_target` and lettering does not require source semantics.

- [ ] **Step 3: Implement the minimal semantic validator and lettering preflight**

Use one exact field set per kind. Do not infer or copy `tail_target` into `speaker_anchor`. Raise `ValueError("balloon-tail-migration-required: ...")` from direct lettering when legacy input reaches the renderer.

- [ ] **Step 4: Migrate valid repository fixtures explicitly**

For human fixture dialogue use `voice_source: "human"` and preserve the fixture’s intentional normalized endpoint as `speaker_anchor`; remove `tail_target`. Captions/SFX omit all dialogue-only fields. Keep dedicated legacy fixtures unchanged.

- [ ] **Step 5: Verify GREEN and commit**

Run the same command; expected all selected tests pass. Commit only schema, fixtures, tests, and docs for this slice.

### Task 2: Deterministic organic-tail geometry and rasterization

**Files:**
- Modify: `scripts/letter_panels.py:540-645,675-891`
- Modify: `tests/test_lettering.py`
- Create: `tests/fixtures/balloon-tails/README.md`

**Interfaces:**
- Produces: `_organic_tail_geometry(rect, speaker_anchor, image_width, image_height, voice_source) -> dict[str, object]`.
- Geometry keys: `policy_version`, `voice_source`, `speaker_anchor`, `attachment`, `base`, `control`, `tip`, `source_gap`, `length`, `width`.
- `_draw_antialiased_balloon(..., tail_geometry | None)` rasterizes a closed cubic silhouette and balloon ellipse into one mask.

- [ ] **Step 1: Write RED geometry tests**

Assert finite/bounded points, one outward ellipse intersection, protected source gap, compact length, narrow base, non-crossing sides, semantic record shape, stable repeated result, and rejection when the anchor lies inside the fitted ellipse.

- [ ] **Step 2: Write RED raster tests**

Render onto a contrasting panel and assert one connected white silhouette, no interior dark seam, continuous outline around the join, caption with no tail, and a visibly tapered tip rather than the old broad wedge ratio.

- [ ] **Step 3: Verify RED**

Run: `/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest tests.test_lettering -v`

Expected: imports/assertions fail because organic geometry is absent and old wedge behavior remains.

- [ ] **Step 4: Implement minimal cubic geometry**

Resolve the ellipse attachment analytically. Clamp tip distance, reserve a panel-relative source gap, derive tangent-aligned base points, and derive two cubic control-point pairs. Reject invalid or self-crossing geometry before drawing.

- [ ] **Step 5: Rasterize one merged supersampled silhouette**

Sample each cubic side deterministically into the local mask, close the path through the base, union it with the ellipse, derive one outline from the merged mask, then downsample with LANCZOS.

- [ ] **Step 6: Verify GREEN and commit**

Run lettering plus typography tests; expected all pass and deterministic fixture hashes remain stable where semantics are unchanged.

### Task 3: Provenance, staleness, and transactional behavior

**Files:**
- Modify: `scripts/letter_panels.py:859-1005`
- Modify: `scripts/validate_project.py:950-1060,1627-1665`
- Modify: `scripts/typography.py:52-67` only if canonical hashing needs a versioned record assertion
- Modify: `tests/test_typography.py`
- Modify: `tests/test_finalization.py`
- Modify: `tests/test_resume.py` or current resume-contract test module

**Interfaces:**
- Lettering geometry item `tail` stores the complete semantic geometry record from Task 2.
- Lettering geometry schema advances to `2.0`; schema `1.0` remains readable but blocks downstream advancement with `balloon-tail-migration-required`.

- [ ] **Step 1: Write RED provenance/staleness tests**

Prove the geometry hash changes for speaker, voice source, anchor, fitted box, dimensions, and policy version; old geometry blocks finalization; changing an anchor invalidates lettering and downstream cache/page/PDF while preserving raw/clean panels.

- [ ] **Step 2: Write RED rollback/resume tests**

Force invalid geometry during re-lettering and prove the prior lettered PNG, geometry, cache, and manifest bytes remain unchanged. Prove a no-change resume reuses current geometry.

- [ ] **Step 3: Verify RED, implement, and verify GREEN**

Run targeted typography/finalization/resume modules. Update geometry validation fail-closed and preserve existing `ProjectTransaction` boundaries. Commit this slice.

### Task 4: Bounded page-QA attribution evidence

**Files:**
- Modify: `scripts/page_quality.py:122-259`
- Modify: `scripts/quality_records.py` only if stricter region validation belongs in the shared record validator
- Modify: `tests/test_page_quality.py`
- Modify: `references/schemas.md:257 onward`
- Modify: `references/workflow.md` page-review instructions

**Interfaces:**
- `bubble-tail-direction.regions` contains exactly one entry per dialogue geometry item.
- Required region keys: `panel_id`, `item_id`, `speaker`, `voice_source`, `balloon_region`, `observed_endpoint_region`, `points_to_declared_source`, `avoids_face_text_action`, `continuous_join`.

- [ ] **Step 1: Write RED bounded-evidence tests**

Reject missing/extra/duplicate item regions, wrong speaker/source, generic evidence, false booleans paired with `pass`, and any caption reported as a tailed dialogue. Accept exact item-complete reviewer evidence bound to current lettering hashes.

- [ ] **Step 2: Verify RED, implement cross-checking, and verify GREEN**

Derive expected IDs and semantics from current lettering geometry. Preserve subjective reviewer ownership; do not infer visual pass from deterministic points. Run page-quality/finalization tests and commit.

### Task 5: Visual proof, docs, packaging, and delivery

**Files:**
- Create: deterministic local render fixture/output under a temporary test directory; commit only compact source/README unless an approved golden artifact is required
- Modify: `SKILL.md`
- Modify: `references/workflow.md`
- Modify: `references/schemas.md`
- Modify: relevant release/package member contracts only when runtime membership changes

**Interfaces:**
- A local-only fixture command renders human-left/right and device-source cases at production panel sizes.
- Visual evidence is retained separately from deterministic mechanics disclosure.

- [ ] **Step 1: Render actual before/after fixture evidence**

Render the old wedge using the RC3 tag into a temporary baseline and the branch result from identical panel/text inputs. Inspect at full resolution for attribution, smooth join, taper, outline consistency, source gap, and obstruction.

- [ ] **Step 2: Iterate only through new RED visual-mechanics regressions**

If inspection exposes a deterministic defect, first encode the mechanical failure as a test, confirm RED, then adjust one geometry variable and rerender. Subjective preference alone is documented rather than fabricated as a deterministic assertion.

- [ ] **Step 3: Run focused and full verification**

Run lettering, validation, typography, page quality, finalization, resume, MCP, and clean-install suites; then full `unittest discover`, `compileall`, build wheel/sdist, `python -m comic_sol_product.release dist/*`, clean-install base/MCP, exact 17-tool smoke, and `git diff --check`.

- [ ] **Step 4: Deliver through review gates**

Commit specific files, push feature branch, open PR to `ai/post-event-development`, require all cross-platform checks, squash merge, rerun merged-commit acceptance, and publish a new prerelease only after all release identity/contracts and public asset verification pass.
