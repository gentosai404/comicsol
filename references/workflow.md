# Comic Sol workflow

## Input detection and project boundary

Choose mode in this order:

1. `resume` takes precedence when the request names an existing directory containing
   `project.json` and says resume, continue, retry, or finish.
2. `source_file` applies to an existing named `.txt` or `.md` file. Require readable
   UTF-8, at most 200 KiB, and preserve its exact bytes.
3. `pasted_story` applies to narrative prose of at least 120 characters or two paragraph
   breaks.
4. Otherwise use `short_prompt`.

Reject a missing file, invalid UTF-8, unsupported extension, or oversized source before
initialization. Generated files stay below the chosen project directory: `project.json`,
`source/`, `plan/`, `references/`, `prompts/`, `panels/`, `qa/`, `pages/`, `exports/`, and
`logs/`. Never overwrite an unrelated directory.

## Materially missing questions

Ask only when one of exactly four conditions holds:

1. The source is unreadable or the intended source among multiple named files is ambiguous.
2. The requested page count exceeds 4 or panel count exceeds 12; offer truncation.
3. The content's audience rating is materially ambiguous because it contains explicit
   sexual content, graphic gore, or an apparently real minor.
4. The output directory exists but is not a valid Comic Sol project and writing could
   overwrite unrelated files.

Otherwise continue with these defaults:

- Pages: 2
- Panels: 4–8, at most 4 per page
- Reading direction: Left-to-right
- Page: 1600 × 2400 px portrait
- Geometry: 32 px gutter and 64 px outer margin
- Direction: original high-contrast manga/anime with expressive ink-like linework and
  restrained color accents
- Rating: Teen, without explicit sex or graphic gore
- Language: source language
- Output root: `./comic-sol-output/`
- Retry: 2 regenerations per panel and 8 extra calls project-wide

Give a short interpretation and announce page/panel count before generation, but do not
pause unless a material condition applies.

## Ten stages

### 1. Detect and initialize

Run `comic_sol.py doctor`, then `comic_sol.py init` with exact source/request files. For
resume, run `comic_sol.py status` and `comic_sol.py resume-plan`; use `comic_sol.py
invalidate` only from the earliest stale stage. Initialization creates the generated
directory boundary and `INIT` manifest.

### 2. Plan story and characters

Write canonical `plan/story-plan.json` and `plan/character-bible.json` using the schemas
and creative reference. Run `validate_project.py PROJECT_DIR --stage plan`, revise invalid
semantic content, then `comic_sol.py transition PROJECT_DIR PLANNED`.

### 3. Script and storyboard

Write dialogue, captions, SFX, pacing, camera, light, continuity, fixed layouts, and
absolute rectangles to `plan/storyboard.json`. Transition through `SCRIPTED`, validate
with `validate_project.py PROJECT_DIR --stage storyboard`, then transition to
`STORYBOARDED`.

### 4. Detect image capability

Follow the capability reference. Record neutral feature flags in `project.json`. If none
is available, transition to `BLOCKED` with the exact preservation error. Do not create
empty image files.

### 5. Generate canonical references

Generate and inspect one canonical reference for each recurring character. Generate a
scene reference only at the creative threshold. Preserve prompts and transition to
`REFERENCES_READY` only when references are usable.

### 6. Generate panels

Write each ordered prompt, invoke the selected agent tool into an attempt file, then run
`comic_sol.py record-attempt`. Confirm readable raster output and at least 512 px in both
dimensions. Never promote before visual QA.

### 7. Visual QA and selective repair

Apply all seven checks from the QA reference with evidence. Retry only failed panels,
retain every attempt, and use one correction clause. Use `comic_sol.py promote-attempt`
for accepted images and `comic_sol.py override-panel` only for an explicit allowed user
override. Validate with `validate_project.py PROJECT_DIR --stage panels`, then transition
through `PANELS_READY` and `QA_READY`.

### 8. Normalize and letter

Prepare clean panel files without semantic edits. Run `letter_panels.py PANEL_DIR
--output-root PATH`; inspect text placement and transition to `LETTERED`.

### 9. Compose and export

Run `compose_pages.py PROJECT_DIR --all`, inspect numeric page PNGs, transition to
`COMPOSED`, run `export_pdf.py PROJECT_DIR`, then transition to `EXPORTED`. Missing panels
or broken pages stop export without replacing a prior good output.

### 10. Final QA and completion

Inspect composed pages, validate with `validate_project.py PROJECT_DIR --stage final`, and
run `render_report.py PROJECT_DIR`. Transition to `COMPLETE` with no unresolved warnings,
`COMPLETE_WITH_WARNINGS` for accepted warning-level impact, or `BLOCKED` for any remaining
error-level failure.

The success path is:

`INIT → PLANNED → SCRIPTED → STORYBOARDED → REFERENCES_READY → PANELS_READY → QA_READY → LETTERED → COMPOSED → EXPORTED → COMPLETE`

## Failure taxonomy

- Invalid input: stop before initialization and name the path, encoding, or size issue.
- Invalid semantic artifact: retain earlier stages, identify file/field, and revise it.
- Capability unavailable: preserve plans, transition `BLOCKED`, and give enable/resume
  instructions.
- Safety refusal: do not evade; record only a sanitized category and transition `BLOCKED`.
- Quota/transient failure: permit one bounded repeat, then preserve and block.
- Invalid image: retain the attempt and selectively retry within budget.
- Visual QA failure: repair only the failed panel; passing hashes remain unchanged.
- Lettering/glyph overflow: preserve images and revise supported text downstream only.
- Missing/stale/corrupt artifact: invalidate its earliest owning stage and downstream.
- Composition/PDF failure: retain lettered panels and rerun only deterministic outputs.

## Completion response

Report final status, pages, panels, generation/retry count, and unresolved warnings. Give
clickable PDF path, page directory, manifest path, and QA report path. State
`COMPLETE_WITH_WARNINGS` plainly; never present `BLOCKED` as partial success.
