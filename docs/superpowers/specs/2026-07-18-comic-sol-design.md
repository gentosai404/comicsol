# Comic Sol Product Design Specification

**Date:** 2026-07-18
**Track:** OpenAI Build Week 2026 — Developer Tools
**Product form:** Portable, installable Agent Skill
**Primary runtime:** Codex with GPT-5.6 Sol
**Delivery scope:** Solo-developer build completed in three days

## 1. Product thesis

Comic Sol turns one natural-language request—or a supplied `.txt` or `.md` story—into a coherent, editable manga/anime comic project. It orchestrates an agent-accessible image generator, then performs the deterministic work that image models do poorly: preserving artifact state, checking panels, placing text, composing pages, exporting a PDF, and explaining quality decisions.

The product is a Codex Skill, not an application around Codex. The agent is the conversational interface and creative director; files in the generated project are the durable user interface. This makes the submission useful in an existing developer workflow, portable across compatible agent hosts, and demonstrably more than a prompt wrapper.

### Target user

The primary user is a writer, indie creator, educator, or developer who has a short story idea but lacks the time or illustration/layout expertise to turn it into a readable visual sequence. They are comfortable invoking a skill in natural language and inspecting files, but should not need to understand prompting, image APIs, page geometry, or publishing software.

The Build Week judge is a critical secondary user. A judge must be able to install the repository, invoke Comic Sol once, and see a non-trivial end-to-end result without rebuilding a service or configuring secrets owned by Comic Sol.

## 2. Product principles

1. **One request starts the whole job.** The skill asks only questions whose answers materially affect whether a valid comic can be produced.
2. **Artifacts are the product.** Every creative and deterministic stage writes inspectable, editable files.
3. **Consistency is explicit.** Character fingerprints, canonical reference images, scene anchors, and continuity checks are first-class data.
4. **Generation is capability-driven.** Comic Sol discovers an agent-provided image capability and never embeds provider credentials or assumes one API.
5. **Deterministic after pixels.** Text placement, layout, page composition, export ordering, hashing, and state transitions are reproducible.
6. **Repair narrowly.** QA failures regenerate only affected panels; successful work is retained.
7. **Honest quality.** The final QA report identifies unresolved warnings rather than claiming perfection.
8. **Original by default.** Prompts describe visual traits and cinematic language, not living artists or protected franchises.

## 3. Goals and non-goals

### Goals

- Accept a short prompt, pasted prose, or a local UTF-8 `.txt`/`.md` file.
- Produce a complete comic project containing panel PNGs, composed page PNGs, a PDF, a manifest, creative intermediates, and a human-readable QA report.
- Derive a compact story plan, character bible, scripted scenes, panel storyboard, and continuity anchors.
- Maintain recognizable characters and stable locations across panels using canonical references and structured prompt anchors.
- Use an image-generation skill/tool exposed to the agent, selected through capability detection rather than hardcoded provider code or secrets.
- Visually inspect generated panels, record evidence, and selectively regenerate failures within a bounded retry budget.
- Place dialogue, captions, and SFX deterministically without relying on generated text inside images.
- Resume safely after interruption and make repeat invocations idempotent when inputs and stage versions are unchanged.
- Work as an installable, self-contained skill with Python 3.11 standard library plus Pillow only.
- Provide clear setup, support, test, and image-capability failure instructions in the package documentation.

### Non-goals

- A web app, server, dashboard, hosted API, account system, database, or standalone SaaS.
- A full digital painting, vector lettering, or desktop publishing suite.
- Long-form graphic novels. The must-have path supports 1–4 pages and no more than 12 panels per run.
- Training, fine-tuning, LoRA creation, face swapping, or custom model hosting.
- Pixel-identical characters across every pose; the promise is recognizable continuity with transparent QA.
- Provider-specific image API integration or automatic secret management.
- Interactive canvas editing, WYSIWYG bubble dragging, collaboration, or cloud storage.
- OCR-dependent extraction of text from generated images.
- Automatic translation, print-press color management, EPUB/CBZ export, animation, or voice.
- Mimicking a named living artist, studio house style, or copyrighted franchise.

## 4. Considered approaches

### Approach A — Monolithic agent prompt

One large `SKILL.md` instructs the agent to plan, generate, inspect, and assemble everything in a single conversational pass.

**Advantages:** fastest prototype; minimal code; demonstrates model orchestration directly.
**Disadvantages:** weak resume behavior, inconsistent filenames, no stable schemas, little deterministic testing, high context pressure, and poor evidence that failed panels alone were repaired.

### Approach B — Provider-bound Python application

A Python CLI calls one image API directly and owns the full pipeline.

**Advantages:** predictable control flow and easy automated invocation.
**Disadvantages:** requires secrets, locks the product to a provider, bypasses the agent’s existing image tools, complicates judge setup, and turns the submission into a standalone application rather than a pure skill.

### Approach C — Selected: agent-orchestrated, artifact-first skill

`SKILL.md` gives the agent a compact state machine and progressively discloses references. The agent performs semantic planning and invokes whatever compatible image capability is available. Small Python scripts validate structured artifacts, compose images, letter panels, export PDF, hash inputs, and report state. JSON files and PNGs form the interface between semantic and deterministic stages.

**Advantages:** preserves the native Codex experience, remains portable, exposes meaningful engineering, supports resume and selective repair, and keeps secrets outside the repository. It is achievable in three days because scripts handle only deterministic operations while the model handles interpretation and visual judgment.
**Disadvantages:** capability discovery differs among agent hosts; visual QA cannot be fully automated; correct orchestration relies on explicit skill instructions. These risks are bounded by a capability contract, fixtures, stage validation, and clear failure messages.

## 5. Selected architecture

Comic Sol is a directory conforming to portable Agent Skills conventions. Its runtime has two cooperating planes:

- **Agent plane:** input interpretation, materially necessary questions, story development, prompt construction, image-capability selection, image generation, visual inspection, QA decisions, and retry decisions.
- **Deterministic plane:** schema validation, canonical hashing, state transitions, geometry calculation, text fitting, bubble/caption/SFX drawing, page composition, PDF export, and report rendering.

The filesystem is the handoff boundary. The agent must write a valid artifact before starting the next stage. Deterministic scripts reject invalid or stale inputs and never silently repair semantic content.

### Runtime state machine

`INIT → PLANNED → SCRIPTED → STORYBOARDED → REFERENCES_READY → PANELS_READY → QA_READY → LETTERED → COMPOSED → EXPORTED → COMPLETE`

A run may also be `BLOCKED` or `COMPLETE_WITH_WARNINGS`. Each transition is written atomically to the manifest only after the stage outputs validate. Resume begins at the earliest invalid or incomplete stage, not simply the last named stage.

## 6. Package and component boundaries

The implementation plan must preserve these boundaries. Files marked “generated project” are outputs, not files committed as sample production output.

```text
comic-sol/
├── SKILL.md
├── LICENSE
├── README.md
├── references/
│   ├── workflow.md
│   ├── creative-direction.md
│   ├── capability-detection.md
│   ├── visual-qa.md
│   ├── safety-ip.md
│   └── schemas.md
├── scripts/
│   ├── comic_sol.py
│   ├── validate_project.py
│   ├── compose.py
│   ├── lettering.py
│   ├── export_pdf.py
│   └── render_report.py
├── templates/
│   ├── manifest.json
│   ├── character-bible.json
│   ├── story-plan.json
│   ├── storyboard.json
│   ├── panel-record.json
│   └── qa-report.md.tmpl
├── assets/
│   ├── fonts/
│   │   └── NotoSans-Regular.ttf
│   └── README.md
└── tests/
    ├── fixtures/
    ├── test_manifest.py
    ├── test_validation.py
    ├── test_lettering.py
    ├── test_compose.py
    ├── test_export_pdf.py
    ├── test_resume.py
    └── test_report.py
```

### Committed component responsibilities

- `SKILL.md`: trigger-focused frontmatter, invocation contract, concise state-machine instructions, and links to references. It contains no long schema copies.
- `references/workflow.md`: stage-by-stage agent procedure, required commands, gates, and resume behavior.
- `references/creative-direction.md`: story planning, camera/pacing vocabulary, prompt-anchor construction, and originality rules.
- `references/capability-detection.md`: detection protocol, compatible capability contract, reference-image handling, and exact unavailable-capability error.
- `references/visual-qa.md`: inspection rubric, severity rules, retry policy, and reporting examples.
- `references/safety-ip.md`: content boundaries, privacy handling, and disallowed style-reference transformations.
- `references/schemas.md`: normative field definitions and schema versioning.
- `scripts/comic_sol.py`: deterministic project initialization, manifest updates, stage invalidation, canonical hashes, status inspection, and resume-plan output. It does not call a model or image provider.
- `scripts/validate_project.py`: cross-file schema and referential-integrity validation.
- `scripts/lettering.py`: deterministic rendering of bubbles, captions, tails, and SFX onto clean panel images.
- `scripts/compose.py`: deterministic placement of lettered panels into page canvases.
- `scripts/export_pdf.py`: ordered page-PNG-to-PDF conversion with embedded raster pages.
- `scripts/render_report.py`: converts structured QA records into a human-readable Markdown report.
- `templates/`: valid versioned starting artifacts copied during initialization.
- `assets/fonts/NotoSans-Regular.ttf`: redistributable pinned font used for deterministic Latin-script lettering; its license and provenance are recorded in `assets/README.md`.
- `tests/`: `unittest` tests for every deterministic script, using tiny synthetic fixtures and golden geometry assertions rather than image-generation calls.

### Generated project boundary

```text
<output>/<slug>/
├── project.json
├── source/
│   ├── input.txt
│   └── request.json
├── plan/
│   ├── story-plan.json
│   ├── character-bible.json
│   └── storyboard.json
├── references/
│   ├── characters/<character-id>.png
│   └── scenes/<scene-id>.png
├── prompts/
│   ├── references/<id>.txt
│   └── panels/<panel-id>.txt
├── panels/
│   ├── raw/<panel-id>.png
│   ├── clean/<panel-id>.png
│   └── lettered/<panel-id>.png
├── qa/
│   ├── panels/<panel-id>.json
│   └── report.md
├── pages/
│   └── page-001.png
├── exports/
│   └── <slug>.pdf
└── logs/
    └── events.jsonl
```

`raw` preserves every accepted generator result. `clean` is an immutable copy or crop normalized for lettering. A failed attempt is retained as `raw/<panel-id>.attempt-<n>.png`; the accepted attempt alone occupies `<panel-id>.png`. Agent-authored prompts are preserved exactly.

## 7. Invocation UX and input modes

### Natural-language entry points

Examples that must trigger the skill:

- “Make a 3-page manga about a courier delivering sunlight to an underground city.”
- “Turn `stories/last-train.md` into a short anime comic.”
- “Create a one-page comic from this: …”
- “Resume the comic in `output/last-train`.”

One invocation is sufficient to begin and, when defaults are acceptable and image generation is available, finish the job. The agent does not require the user to run scripts manually.

### Input-mode detection

Detection is ordered and deterministic:

1. If the request names an existing local `.txt` or `.md` file, mode is `source_file`; read it as UTF-8 and preserve an exact copy in `source/input.txt`.
2. Else if the request contains at least 120 characters of narrative prose or two paragraph breaks, mode is `pasted_story`.
3. Else mode is `short_prompt`.
4. If the request identifies an existing project directory containing `project.json` and uses “resume,” “continue,” “retry,” or “finish,” mode is `resume` and takes precedence.

Only `.txt` and `.md` source files are accepted in the must-have version. Missing files, invalid UTF-8, and files over 200 KiB produce clear errors before project creation.

### Questions and defaults

The agent asks a question only if one of these conditions holds:

- The source is unreadable or the intended source among multiple named files is ambiguous.
- Requested page count exceeds 4 or panel count exceeds 12; the agent offers truncation to the supported maximum.
- The content’s audience rating is materially ambiguous because it includes explicit sexual content, graphic gore, or an apparently real minor.
- The output directory exists but is not a valid Comic Sol project, so writing could overwrite unrelated files.

All other omissions use defaults:

| Setting | Default |
|---|---|
| Pages | 2 |
| Panels | Agent chooses 4–8, maximum 4 per page |
| Reading direction | Left-to-right |
| Page size | 1600 × 2400 px portrait |
| Gutter / outer margin | 32 px / 64 px |
| Visual direction | Original high-contrast manga/anime, expressive ink-like linework, restrained color accents |
| Rating | Teen; no explicit sex or graphic gore |
| Language | Input language for prose and dialogue |
| Output root | `./comic-sol-output/` |
| Retry budget | 2 regenerations per panel, 8 extra calls project-wide after initial reference and panel calls |

Before generation, the agent gives a one-paragraph interpretation and announces chosen page/panel count, but does not pause for confirmation unless a material-question condition applies.

### Completion response

The agent reports the final status, page and panel counts, retry count, unresolved warnings, and clickable paths to the PDF, page directory, manifest, and QA report. It does not hide a `COMPLETE_WITH_WARNINGS` result behind success language.

## 8. Normative data schemas

All JSON files use UTF-8, two-space indentation, newline at EOF, ISO 8601 UTC timestamps, stable key ordering when written by scripts, and schema version string `1.0`. Unknown fields are rejected in deterministic validation for version `1.0`. IDs match `^[a-z][a-z0-9-]{0,47}$`.

### 8.1 Project manifest: `project.json`

```json
{
  "schema_version": "1.0",
  "project_id": "sunlight-courier",
  "title": "The Sunlight Courier",
  "created_at": "2026-07-18T04:00:00Z",
  "updated_at": "2026-07-18T04:18:00Z",
  "status": "PANELS_READY",
  "input": {
    "mode": "short_prompt",
    "source_path": "source/input.txt",
    "source_sha256": "64-lowercase-hex",
    "request_path": "source/request.json",
    "language": "en"
  },
  "settings": {
    "page_width": 1600,
    "page_height": 2400,
    "reading_direction": "ltr",
    "page_count": 2,
    "panel_count": 7,
    "style_anchor": "original high-contrast manga/anime; expressive ink-like linework; restrained amber accents",
    "max_panel_retries": 2
  },
  "capability": {
    "status": "available",
    "name": "agent-image-generation",
    "supports_reference_images": true,
    "supports_dimensions": true,
    "detected_at": "2026-07-18T04:01:00Z"
  },
  "artifacts": {
    "story_plan": {"path": "plan/story-plan.json", "sha256": "64-lowercase-hex"},
    "character_bible": {"path": "plan/character-bible.json", "sha256": "64-lowercase-hex"},
    "storyboard": {"path": "plan/storyboard.json", "sha256": "64-lowercase-hex"},
    "qa_report": {"path": "qa/report.md", "sha256": "64-lowercase-hex"},
    "pdf": {"path": "exports/sunlight-courier.pdf", "sha256": "64-lowercase-hex"}
  },
  "stage_versions": {
    "planning": "1",
    "storyboard": "1",
    "generation": "1",
    "lettering": "1",
    "composition": "1",
    "export": "1"
  },
  "panels": ["p01-01", "p01-02", "p01-03", "p02-01", "p02-02", "p02-03", "p02-04"],
  "warnings": []
}
```

Allowed status values are the state-machine states in Section 5. Artifact entries may be absent until produced; they may never contain an empty path or a non-SHA-256 sentinel value.

### 8.2 Character bible: `plan/character-bible.json`

```json
{
  "schema_version": "1.0",
  "characters": [
    {
      "id": "mira",
      "name": "Mira",
      "role": "protagonist courier",
      "age_band": "young-adult",
      "pronouns": "she/her",
      "visual_fingerprint": {
        "silhouette": "short, compact build; oversized square courier bag",
        "face": "round face; wide-set dark eyes; straight brows; small nose",
        "hair": "chin-length black bob; single upward cowlick; blunt fringe",
        "wardrobe": "cream cropped jacket; charcoal utility trousers; amber scarf",
        "palette": ["charcoal", "cream", "amber"],
        "signature_props": ["square courier bag", "sun-vial on brass chain"],
        "invariants": ["cowlick points left", "scarf is amber", "bag has circular clasp"],
        "avoid": ["photorealism", "logos", "different hair length", "generated text"]
      },
      "personality": ["resourceful", "guardedly hopeful"],
      "motivation": "complete the final delivery before the city lights fail",
      "speech": "short practical sentences; avoids exclamation marks",
      "reference_path": "references/characters/mira.png"
    }
  ]
}
```

Every speaking or recurring character needs a record. `visual_fingerprint` fields are concrete visible traits, not subjective adjectives alone. `invariants` contain 2–5 panel-checkable facts. One-off background figures need no bible entry.

### 8.3 Story plan: `plan/story-plan.json`

```json
{
  "schema_version": "1.0",
  "title": "The Sunlight Courier",
  "logline": "A courier races to deliver the last vial of sunlight to a failing underground district.",
  "theme": "Hope is meaningful when it is shared.",
  "tone": ["urgent", "tender", "luminous"],
  "rating": "teen",
  "setting": "A layered underground city powered by bottled daylight.",
  "beginning": "Mira receives the last sun-vial as the public lights flicker.",
  "turn": "A collapsed bridge blocks the direct route.",
  "climax": "Mira swings across the generator shaft using her courier line.",
  "ending": "The district relights and neighbors share the glow.",
  "scenes": [
    {
      "id": "delivery-hall",
      "purpose": "establish stakes and launch the delivery",
      "location": "brass dispatch hall",
      "time": "artificial dusk",
      "characters": ["mira"],
      "continuity_anchor": "ribbed brass walls; numbered round doors; failing amber ceiling strips"
    }
  ]
}
```

The plan has 2–5 scenes and a complete beginning/turn/climax/ending. Every storyboard scene references one listed scene.

### 8.4 Storyboard: `plan/storyboard.json`

```json
{
  "schema_version": "1.0",
  "pages": [
    {
      "number": 1,
      "layout": "hero-top-two-bottom",
      "panels": [
        {
          "id": "p01-01",
          "order": 1,
          "scene_id": "delivery-hall",
          "rect": {"x": 64, "y": 64, "width": 1472, "height": 1176},
          "beat": "The lights fail as Mira receives the vial.",
          "characters": ["mira"],
          "shot": "wide establishing shot, slight low angle",
          "composition": "Mira on right third; dispatch doors recede left; clear dark ceiling area for caption",
          "action": "Mira catches the glowing vial with both hands.",
          "expression": "focused surprise",
          "lighting": "single amber vial as key light; ceiling strips fading",
          "continuity": ["mira:scarf is amber", "delivery-hall:numbered round doors"],
          "negative": ["text", "speech bubbles", "watermark", "extra fingers", "duplicate character"],
          "text": [
            {
              "id": "p01-01-t01",
              "kind": "caption",
              "speaker": null,
              "content": "Below the clouds, daylight had become a delivery.",
              "anchor": "top-left",
              "tail_target": null,
              "priority": 1
            }
          ]
        }
      ]
    }
  ]
}
```

`rect` coordinates are absolute page pixels and must remain inside the page margin without overlap. Panel IDs encode page and reading order. Layout is selected from the fixed presets in Section 11. Each panel has 0–3 text items, at most 45 words total, and dialogue speakers must appear in `characters`. `anchor` is one of `top-left`, `top-center`, `top-right`, `middle-left`, `middle-right`, `bottom-left`, `bottom-center`, or `bottom-right`.

### 8.5 Panel record: `qa/panels/<panel-id>.json`

```json
{
  "schema_version": "1.0",
  "panel_id": "p01-01",
  "source_prompt_path": "prompts/panels/p01-01.txt",
  "raw_path": "panels/raw/p01-01.png",
  "clean_path": "panels/clean/p01-01.png",
  "raw_sha256": "64-lowercase-hex",
  "dimensions": {"width": 1472, "height": 1176},
  "attempts": 1,
  "generation": {
    "capability_name": "agent-image-generation",
    "reference_paths": ["references/characters/mira.png"],
    "completed_at": "2026-07-18T04:10:00Z"
  },
  "checks": [
    {"id": "character-identity", "result": "pass", "severity": "error", "evidence": "bob, cowlick, scarf, and bag clasp match reference"},
    {"id": "text-free", "result": "pass", "severity": "error", "evidence": "no visible lettering or watermark"},
    {"id": "composition", "result": "pass", "severity": "error", "evidence": "caption-safe dark region remains at top-left"}
  ],
  "decision": "accept",
  "retry_reason": null,
  "unresolved_warnings": []
}
```

Check results are `pass`, `fail`, or `warning`; severities are `error` or `warning`; decisions are `accept`, `regenerate`, or `accept_with_warnings`. A regeneration increments `attempts`, preserves the prior image, replaces checks with checks for the newest attempt, and records the old decision in the event log.

Every accepted panel record must contain exactly these seven check IDs: `character-identity`, `anatomy`, `action`, `composition`, `continuity`, `text-free`, and `technical`. `character-identity` is `pass` when no recurring character is present. `technical` verifies a readable raster, minimum dimensions, correct aspect-ratio tolerance of ±2%, and absence of unintended transparency. The sample above abbreviates the list only to keep the schema example readable; normative validation requires all seven.

### 8.6 QA report: `qa/report.md`

The report is Markdown generated from the manifest and panel records with these required sections:

1. Project summary and final status.
2. Capability used and whether reference images were supported.
3. Counts: pages, panels, generation attempts, regenerated panels, accepted warnings, and hard failures.
4. A panel table with panel ID, attempt count, decision, character, anatomy, continuity, composition, and text-free results.
5. Unresolved warnings with user-visible impact.
6. Artifact integrity results: dimensions, hashes present, valid references, ordered pages, and PDF open/read check.
7. Resume statement listing reused versus regenerated artifacts.

The structured panel records are the machine-readable QA schema; `report.md` is its human-readable projection. A report may say “no unresolved warnings,” but the section must exist.

## 9. Pipeline and data flow

### Stage 1 — Detect and initialize

The agent selects the input mode, reads the source, applies defaults, and invokes `comic_sol.py init`. Initialization creates a new slugged project directory using exclusive creation, copies the exact input, writes normalized settings, calculates source/request hashes, and logs `project.created`.

### Stage 2 — Plan story and characters

The agent produces `story-plan.json` and `character-bible.json`, then runs validation. Character entries contain stable visual fingerprints before any image is generated. Invalid artifacts are revised in place before proceeding.

### Stage 3 — Script and storyboard

The agent converts story beats into concise dialogue/captions and selects fixed page-layout presets. It writes every panel’s beat, camera, action, expression, lighting, continuity constraints, negative constraints, text payload, and absolute rectangle to `storyboard.json`. Validation checks page bounds, IDs, word budgets, references, and overlap.

### Stage 4 — Detect image capability

Before making image prompts, the agent follows Section 10. If no compatible capability exists, it marks the run `BLOCKED`, writes an actionable error and event, and stops without fabricating empty panel files.

### Stage 5 — Generate canonical references

For each recurring character, the agent constructs a neutral full-body reference prompt from the fingerprint: front three-quarter pose, readable clothing/props, plain background, no lettering. It generates one canonical reference PNG. A scene reference is generated only for a location appearing in three or more panels; otherwise its text continuity anchor is sufficient. Reference images are checked for their declared invariants before use.

### Stage 6 — Generate panels

The agent writes each final prompt to `prompts/panels/<id>.txt`. The prompt concatenates, in order: project style anchor, scene continuity anchor, exact character fingerprints, panel action/expression, camera/composition/lighting, reserved text-safe areas, and negative constraints. If the capability supports image references, all on-panel character references and the applicable scene reference are supplied. Generation asks for the panel rectangle’s aspect ratio and no embedded text.

### Stage 7 — Visual QA and selective regeneration

The agent visually inspects each raw PNG against the storyboard and reference images. It writes a panel record before deciding. Error-level failure triggers regeneration of that panel only using the original prompt plus one precise corrective sentence. Warnings do not trigger retries unless they impair readability. The retry budget is enforced as specified in Section 12.

### Stage 8 — Normalize and letter

Accepted images are EXIF-transposed, converted to RGB, and center-cropped only when necessary to the exact storyboard aspect ratio; no semantic inpainting occurs. `lettering.py` renders declared text onto clean copies using deterministic geometry.

### Stage 9 — Compose and export

`compose.py` places lettered panels on white page canvases in storyboard order, applying gutters and black panel borders. `export_pdf.py` combines page PNGs in numeric order. Scripts validate dimensions and reject missing panels rather than producing partial final output.

### Stage 10 — Final QA and completion

The agent checks composed pages for reading order, clipped/overlapping text, bubble tails, borders, and page continuity. Deterministic integrity checks validate all hashes and open the PDF with Pillow. `render_report.py` writes the report. The manifest becomes `COMPLETE` when there are no warnings, `COMPLETE_WITH_WARNINGS` when accepted warning-level issues remain, or `BLOCKED` when any error-level issue remains after retries.

## 10. Image capability detection and contract

Capability detection is an agent procedure because portable Skill packages cannot enumerate every host’s tools from Python.

The agent performs these steps in order:

1. Inspect its currently exposed skills/tools for an image-generation or image-editing capability that returns or writes a raster image.
2. Prefer a capability that accepts reference images; next prefer requested dimensions or aspect ratio; then prefer one that writes PNG directly.
3. Record a neutral capability name and booleans for `supports_reference_images` and `supports_dimensions` in the manifest. Never record tokens, environment values, or provider secrets.
4. Perform no speculative network call merely to detect availability. The first canonical-reference generation is the operational check.
5. After a capability invocation, verify that the declared local output exists, is a readable PNG/JPEG/WebP, and has both dimensions at least 512 px. Normalize it to PNG through Pillow.

A compatible capability must accept a text prompt and yield an agent-accessible raster file. Reference-image and dimension support are optional. When references are unsupported, the agent strengthens text anchors and the report records the degraded consistency mode. An editing-only capability is insufficient unless it can create the first reference image from text.

Comic Sol does not read environment variables for image credentials, import provider SDKs, or instruct the user to paste a secret into chat.

If no compatible capability is exposed, the exact leading error is:

> Comic Sol cannot generate panels because this agent session has no compatible text-to-image capability. Enable or install an image-generation skill/tool that can return a local raster image, then say “resume this Comic Sol project.” Your story plan and editable project files have been preserved at the project path printed below.

The next line contains the resolved absolute project path; it is data, not part of the fixed leading error.

Tool refusal, quota exhaustion, and provider errors use the same preservation behavior but report the actual sanitized failure category and resume instruction.

## 11. Consistency and deterministic presentation

### Character and scene consistency

Consistency uses four reinforcing layers:

1. **Structured fingerprints:** the same exact visible-trait strings are reused in every relevant prompt; the agent does not paraphrase them panel by panel.
2. **Canonical references:** one approved neutral image per recurring character, supplied to generation when supported.
3. **Scene anchors:** stable architecture, palette, time, and light-source facts are repeated exactly. A visual scene reference is added only when reuse justifies the generation cost.
4. **Continuity QA:** every panel’s declared invariants are explicitly checked, with evidence, before acceptance.

References are immutable within a run after the first dependent panel is accepted. Changing a fingerprint or reference invalidates all dependent panels, pages, PDF, and QA outputs. Changing dialogue alone invalidates lettering, pages, PDF, and final report, but retains raw and clean panels.

### Fixed layout presets

The must-have system exposes five presets: `full-page`, `two-horizontal`, `three-horizontal`, `hero-top-two-bottom`, and `two-top-hero-bottom`. Rectangles are calculated from the 1600 × 2400 page, 64 px margin, and 32 px gutters. No panel overlaps, rotated panels, bleeds, or inset panels are allowed in the must-have tier. The agent selects the preset based on pacing; exact geometry comes from the deterministic initializer/validator.

### Text sanitation

- Dialogue/caption content is Unicode NFC-normalized.
- Control characters other than newline are rejected.
- Dialogue is limited to 32 words per item; captions to 45 words; SFX to 3 words.
- Newlines in source text are treated as optional break hints, not forced layout.
- Straight quotes are rendered as provided; the script does not rewrite authored punctuation.
- Unsupported glyphs in the bundled font cause a blocking lettering error naming the characters and recommending user-supplied text in the supported Latin/Greek/Cyrillic range for the must-have build.

### Bubble and caption placement

Lettering operates inside each panel’s pixel coordinates after normalization:

- Each anchor maps to a rectangular candidate zone occupying 42% of panel width and 30% of panel height, inset by 4% on all panel edges.
- Text items are placed by ascending `priority`, then ID. Items sharing a zone stack in that order with a 16 px gap.
- Dialogue uses a white ellipse with a 4 px black outline and 24 px internal padding. A triangular tail points toward `tail_target`, expressed as normalized panel coordinates `[x, y]`; if absent, no tail is drawn.
- Captions use a white rectangle with a 4 px black outline, 20 px padding, and square corners.
- SFX uses transparent fill, 6 px white outer stroke, 3 px black inner stroke, and no bubble.
- Font starts at 42 px for dialogue/caption and 64 px for SFX, decreasing by 2 px to a minimum of 24 px. Wrapping is greedy by measured pixel width, preserving explicit paragraph breaks.
- If text does not fit at 24 px, lettering fails with the item ID. It never clips, elides, or silently changes words.
- Candidate zones must not overlap earlier text boxes. If the requested zone is occupied, search follows clockwise anchor order beginning with the requested anchor. Failure after all eight zones blocks the panel and asks the agent to shorten or split authored text automatically while preserving meaning; the revised storyboard is logged and validated.

Text-safe space is requested during image generation, but deterministic placement is authoritative. Since object-aware collision detection is out of scope, final visual QA catches bubbles covering critical faces or actions; the agent may choose another anchor without regenerating the image.

### Page composition and export

- Page canvas is opaque white RGB at exactly 1600 × 2400 px.
- Accepted panels are resized with Pillow LANCZOS to their exact storyboard rectangles.
- A 6 px black border is drawn inward around every panel.
- Page filenames are zero-padded `page-001.png` in numeric order.
- PNGs use Pillow default lossless encoding with metadata omitted.
- PDF pages are RGB, 150 DPI metadata, no additional margins, in numeric page order. The visual resolution remains 1600 × 2400.
- Repeated composition with identical source bytes, Pillow version, bundled font, and stage version must yield identical pixel content; file-level PDF byte identity is not promised because encoder metadata may vary.

## 12. Resume, caching, retries, and failures

### Artifact identity and cache keys

Each stage cache key is SHA-256 over canonical JSON inputs, direct input-file SHA-256 values, and the relevant `stage_versions` value. Canonical JSON means UTF-8, sorted keys, compact separators, and no timestamps. Generated-image identity also includes the exact prompt file hash, reference image hashes, capability feature flags, and attempt number; it does not assume access to a provider seed.

An artifact is reusable only when its file exists, recorded hash matches, schema validates, all dependencies validate, and its stage cache key matches. Otherwise that stage and all downstream stages are invalidated. The event log records `reused`, `invalidated`, `generated`, `failed`, and `accepted` events.

### Idempotency

Running resume twice against a `COMPLETE` project with unchanged inputs performs validation, reports that all artifacts are current, and writes no artifact files or timestamps. Event logging is also skipped for a no-op resume so the project tree remains unchanged.

Initialization against an existing valid project with the same normalized request returns its path and resume status. A differing request never overwrites it; a deterministic `-2`, `-3`, and so on suffix is used. An existing non-project directory is never overwritten.

### Writes and interruption safety

Deterministic scripts write to a sibling temporary file, flush and `fsync`, then use `os.replace`. The manifest transition is last. Images returned by a capability are first written to an attempt filename, validated, and only then promoted to the accepted filename. Interrupted temporary files are ignored and reported on resume; they may be overwritten, not deleted automatically.

### Retry policy

- Initial generation plus at most 2 regenerations per panel.
- A project-wide cap of 8 extra calls after the initial reference and panel calls prevents runaway cost. Visual regenerations and transient-error repeats both consume this shared cap.
- Only error-level visual failures trigger regeneration: wrong/missing principal character, violated fingerprint invariant, severe anatomy that impairs the beat, incorrect action, unreadable composition, embedded text/watermark, or unusable dimensions/corruption.
- Warning-level issues—minor prop drift, small anatomy artifacts, or stylistic variance that does not impair reading—are accepted and reported.
- Each retry adds exactly one correction clause addressing observed failures; it retains all canonical anchors and references.
- Capability failures use exponential conceptual backoff only when the host natively manages retries. Comic Sol itself makes at most one immediate repeat for a transient tool error; this does not consume a visual regeneration attempt but does count toward the global call cap.

After budget exhaustion, an error-level panel leaves the project `BLOCKED`; it is never lettered into a final export. The user can explicitly say “accept panel `<id>` with warnings” to override non-safety visual errors, which records the override and produces `COMPLETE_WITH_WARNINGS`. Corrupt/unreadable images and safety refusals cannot be overridden.

### Failure taxonomy

| Category | Result |
|---|---|
| Invalid/unreadable input | Stop before initialization; identify path/encoding/limit |
| Invalid semantic artifact | Keep prior stages; report file and field; agent revises |
| Image capability unavailable | `BLOCKED`; preserve plans; provide enable-and-resume message |
| Tool refusal/safety refusal | `BLOCKED`; do not evade; record sanitized reason |
| Tool quota/transient error | One bounded repeat, then `BLOCKED`; resume supported |
| Invalid returned image | Preserve attempt; count as error; selectively retry |
| Visual QA failure | Selectively regenerate within budgets |
| Lettering overflow/glyph error | Preserve images; revise text or supported glyphs; rerun downstream only |
| Missing/stale/corrupt artifact | Invalidate earliest affected stage and downstream artifacts |
| PDF/composition error | Retain lettered panels; rerun deterministic stage after correction |

## 13. Privacy, intellectual property, and safety

### Privacy

- All project artifacts remain in the user-selected local output directory except data necessarily sent through the agent’s chosen image capability.
- Before image generation, the skill warns when input appears to contain secrets, credentials, private keys, financial account numbers, or highly specific personal contact data and asks the user to redact it. Detection is best-effort and described honestly.
- Prompts sent for image generation include only the story/visual information required for the panel, not unrelated source text or absolute local paths.
- Logs contain event names, relative paths, hashes, attempt counts, and sanitized error categories; never environment variables, tool arguments containing secrets, or raw provider responses.
- Comic Sol does not promise provider-side deletion or privacy. The completion report identifies that the selected external image capability’s policies govern transmitted prompts and references.

### IP and style safety

- Default art direction uses original descriptive traits such as line weight, contrast, palette, lens, lighting, texture, and era-neutral genre language.
- If the user requests a living artist, active studio, or named franchise style, the agent declines imitation and translates the request into non-identifying visual characteristics. It does not include the protected name in generation prompts.
- Public-domain story adaptation is allowed; user-provided copyrighted text is treated as user-authorized input, but Comic Sol does not claim rights or add licensing assurances.
- The skill does not generate logos, signatures, watermarks, or false creator attribution.
- Outputs include no claim that they are copyrightable, commercially cleared, or free of model-provider restrictions.

### Content safety

- The invoked image capability’s safety policy is authoritative; Comic Sol never retries with euphemisms to bypass a refusal.
- Sexual content involving minors or ambiguous-age young characters is refused and not planned.
- Non-consensual explicit sexual content and instructions for graphic real-world wrongdoing are refused.
- Fictional teen-rated action, suspense, and non-graphic injury are within the default scope.
- Depictions of real people require a user-supplied authorized reference and remain subject to the image capability’s policy; face swapping is out of scope.

## 14. Testing strategy

All deterministic Python uses Python 3.11, `unittest`, `tempfile`, `pathlib`, `hashlib`, `json`, and Pillow. Tests run offline and never call an image service. Pillow is the only non-stdlib runtime/test dependency.

### Unit and contract tests

- **Manifest/state:** valid transitions, rejected skipped transitions, atomic update behavior, canonical hashes, no-op resume, downstream invalidation, and slug collision behavior.
- **Validation:** every required field, unknown-field rejection, ID format, referential integrity, panel bounds/overlap, page/panel maximums, text word limits, and missing files.
- **Layout:** exact rectangles for all five presets at 1600 × 2400; gutters, margins, and reading order.
- **Lettering:** deterministic wrapping, font fallback failure, minimum-size overflow, anchor search order, non-overlap, tail geometry, caption shape, SFX stroke, Unicode normalization, and preservation of authored text.
- **Composition:** exact output dimensions, border placement, panel order, RGB conversion, LANCZOS sizing, missing-panel failure, and stable pixel hashes from synthetic solid-color panels.
- **PDF:** page count/order, readable output, RGB conversion, and rejection of absent pages.
- **QA report:** complete required sections, correct aggregates, unresolved warning rendering, capability degradation disclosure, and resume summary.

### Integration fixtures

Two committed tiny projects exercise the pipeline without model calls:

1. A one-page, three-panel valid fixture with synthetic reference/panel images runs validate → letter → compose → export → report.
2. An interrupted two-page fixture has one valid panel, one failed attempt, and missing downstream artifacts; resume must reuse the valid panel and identify only the missing/failed panel for generation.

The tests assert files, dimensions, manifest status, hashes where deterministic, and QA content. Golden images are limited to tiny crops or pixel assertions to avoid brittle platform-wide PNG byte comparisons.

### Skill-level manual acceptance

On Codex with GPT-5.6 Sol and an image-generation capability, run one short-prompt case and one `.md` case. Observe that the skill triggers naturally, makes no unnecessary question, records capability detection, creates references, repairs at least one deliberately rejected test panel or documents that all passed, and completes all exports. Then remove/disable the image capability and confirm the exact clear-error path preserves planning artifacts.

### Verification command

The future package’s single offline verification command is:

```bash
python3.11 -m unittest discover -s tests -v
```

README installation verification also runs:

```bash
python3.11 scripts/comic_sol.py doctor
```

`doctor` checks Python version, Pillow import/version, bundled font readability, writable output root, templates, and whether capability detection must still occur in the agent session. It does not claim an image tool is present because Python cannot portably inspect agent tools.

## 15. Packaging, installation, and support design

### Portable skill package

The repository root is the skill directory. `SKILL.md` frontmatter contains only:

```yaml
---
name: comic-sol
description: Create a finished manga/anime comic project from a short prompt, pasted story, or local .txt/.md file; use when the user asks to make, storyboard, render, resume, or export a comic with panels, pages, PDF, and visual QA.
---
```

The body stays concise: trigger examples, entry decision tree, state summary, required agent/tool behaviors, and direct links to only the reference needed for the current stage. Detailed schemas and rubrics live in `references/` for progressive disclosure.

### Installation

README later provides two supported methods:

1. Copy or clone the repository directory into the host’s Agent Skills directory, preserving the directory name `comic-sol`.
2. For Codex, copy it to the user’s configured Codex skills directory and restart/reload the session so `SKILL.md` is discovered.

Then install Pillow `11.3.0` into the Python 3.11 environment, run the offline tests, run `doctor`, and start a new agent session exposing an image-generation capability. The implementation records that exact pin in installation documentation to keep layout results reproducible. No build step, database, server, Node toolchain, API key file, or package publication is required.

Exact host-specific path examples must be verified against current official Codex documentation when README is written; the skill itself remains path-agnostic.

### Support contract

Supported baseline: Python 3.11, Pillow 11.3.0, local writable filesystem, UTF-8 `.txt`/`.md` input, and an agent host able to read Skill instructions and expose a text-to-image capability. Windows, macOS, and Linux are targeted through `pathlib`; tests must run on at least Linux and Windows before submission. Issues outside that baseline receive a clear `doctor` diagnostic rather than best-effort silent behavior.

## 16. Build Week evidence and demo strategy

### Repository evidence

- Preserve git history showing all new product work after July 13, 2026; the first Comic Sol implementation commit is dated after that cutoff.
- Keep this design spec, subsequent implementation plan, tests, fixtures, and incremental commits as evidence of a Codex-led build process.
- Before submission, make the repository public and verify it from a logged-out browser.
- README later includes the product thesis, install/test/support steps, architecture, example invocation, sample output thumbnails, limitations, and a concise “Built with Codex and GPT-5.6 Sol” collaboration narrative.
- Add the required `/feedback` Codex Session ID to the submission materials and README only after it exists; this specification intentionally does not invent an ID.
- Judges receive the committed skill and sample outputs; they run tests and invoke it without rebuilding any service.

### Under-three-minute demo

The demo uses a preinstalled skill and a clean session with image generation enabled. Target length is 2:40:

| Time | Demonstration |
|---|---|
| 0:00–0:20 | State the problem and show the repository is a Skill, not a web app |
| 0:20–0:35 | Invoke: “Make a 2-page manga about a courier delivering sunlight to an underground city” |
| 0:35–1:05 | Show live planning artifacts, character fingerprint, storyboard, and detected image capability; jump over generation wait |
| 1:05–1:35 | Show canonical character reference, raw panels, one panel QA failure, and selective regeneration only for that panel |
| 1:35–2:05 | Show deterministic lettering and composed pages, then open the PDF |
| 2:05–2:25 | Open the human-readable QA report and manifest; point out hashes and accepted/retried panels |
| 2:25–2:40 | Run resume to show a no-op cache hit and close on installability/impact |

The demo is rehearsed using committed sample artifacts so network latency cannot consume the presentation, while the screen recording includes a clearly identified live invocation. A second 15-second optional clip shows the no-image-capability error.

### Judging alignment

- **Technological implementation:** capability abstraction, artifact schemas, selective visual QA repair, deterministic composition, resume/cache semantics, and offline tests.
- **Design:** natural-language invocation, minimal questions, editable intermediates, coherent visual anchors, clean outputs, and readable failure/reporting UX.
- **Impact:** compresses writing, art direction, layout, lettering, and export into one accessible workflow for creators without a production team.
- **Idea quality:** a pure skill uses Codex as the product surface and combines generative judgment with deterministic tooling rather than wrapping a chat prompt in a dashboard.

## 17. Acceptance criteria

The must-have product is accepted only when all criteria below are demonstrably true:

1. Installing the repository as a skill and issuing one natural-language comic request triggers Comic Sol without a command syntax requirement.
2. Short prompt, pasted story, `.txt`, `.md`, and resume modes follow the detection rules in Section 7.
3. A default request completes without questions when its input is readable, teen-safe, within limits, and an image capability is available.
4. Output includes valid `project.json`, exact source copy, story plan, character bible, storyboard, reference PNGs, saved prompts, raw/clean/lettered panel PNGs, page PNGs, PDF, structured panel QA, event log, and Markdown QA report.
5. A default run is limited to 1–4 pages, at most 12 panels, at most 4 panels per page, and the fixed layout presets.
6. Every recurring character has a canonical reference and 2–5 concrete invariants; every dependent panel prompt reuses its exact fingerprint.
7. The selected image capability is recorded by features rather than provider secrets; the repository contains no hardcoded image API or credential requirement.
8. With no compatible image capability, the project becomes `BLOCKED`, retains planning artifacts, and emits the exact leading error in Section 10.
9. Each panel receives recorded visual checks for identity, anatomy, action, composition, continuity, text-free output, and technical validity.
10. An error-level failed panel alone is regenerated, its earlier attempt is retained, and passing panels’ hashes remain unchanged.
11. Retry limits and the global call cap are enforced; unresolved errors never appear in a final PDF unless explicitly overridden where allowed.
12. Generated images contain no intentional dialogue; all dialogue, captions, and SFX are placed from storyboard data by deterministic scripts.
13. Text never clips silently. Overflow or unsupported glyphs produce an item-specific blocking error.
14. Page PNGs are 1600 × 2400 RGB, correctly ordered, bordered, and readable; the PDF opens and contains the same number/order of pages.
15. A no-change resume after completion rewrites no artifacts and reports full reuse; changing dialogue invalidates only lettering and downstream stages.
16. All deterministic scripts have offline `unittest` coverage, and the documented test command passes on the submission commit.
17. The QA report distinguishes pass, warning, retry, override, and blocking failure, and names unresolved user-visible issues.
18. Originality, privacy, refusal, logging, and external-capability disclosures match Section 13.
19. The public repository can be installed and tested from its documented instructions without a build service; sample outputs allow judges to inspect results immediately.
20. A rehearsed demo covers invocation, planning, references, selective regeneration, lettering, PDF, QA, and no-op resume in under three minutes.

## 18. Three-day delivery tiers

### Must-have — submission-critical

**Day 1: skill contract and artifacts**

- `SKILL.md`, workflow/capability/creative/safety references, schemas, templates, initializer, validator, state transitions, hashing, resume-plan logic, and tests.
- Short prompt, pasted story, `.txt`, `.md`, and resume input procedures.
- Story plan, character bible, storyboard, manifest, panel QA schemas, and five fixed layouts.

**Day 2: visual pipeline and deterministic production**

- Canonical character references, text-anchor consistency protocol, capability-driven panel generation instructions, visual QA rubric, selective retry behavior, and panel attempt preservation.
- Pillow normalization, deterministic lettering, page composition, PDF export, report rendering, and exhaustive deterministic tests with synthetic fixtures.

**Day 3: integration, evidence, and demo**

- Two end-to-end live acceptance runs, unavailable-capability run, Windows/Linux checks, integration fixtures, failure-message polish, public installation/support/testing documentation, sample outputs, clean-room install rehearsal, and sub-three-minute demo recording.

Must-have deliberately uses only five layouts, one bundled font, Latin/Greek/Cyrillic lettering coverage, raster PDF output, 1–4 pages, and at most 12 panels.

### Stretch — only after must-have acceptance passes

- Right-to-left reading order for the same five layouts, including text priority and page ordering tests.
- One additional bundled CJK-capable font if repository size and redistribution license are acceptable, with deterministic font selection tests.
- Contact-sheet PNG summarizing character references and panels for quick review.
- User-supplied `project-overrides.json` for page count, palette, and typography without editing generated manifests.
- CBZ export implemented as deterministic ZIP packaging of page PNGs.

Stretch work may consume no more than four hours on Day 3 and must not displace demo rehearsal, install verification, or failure-path testing.

### Cut — explicitly excluded from the three-day build

- Web UI, server, dashboard, authentication, cloud persistence, queue, or database.
- Direct image-provider adapters, API-key setup, automatic tool installation, or model training.
- Freeform layouts, drag-and-drop editing, vector bubbles, PSD/SVG/EPUB export, professional print preflight, CMYK, or bleed.
- More than 4 pages/12 panels, multi-chapter continuity, shared universes, or cross-project character libraries.
- OCR, automatic translation, full multilingual typography, handwritten font generation, or vertical-script layout.
- Automated computer-vision scoring, face embeddings, pose control, depth maps, or segmentation-based bubble avoidance.
- Marketplace publishing automation, telemetry, analytics, billing, or collaboration.

## 19. Scope resolution and final design decisions

The product promise is a polished short comic, not arbitrary-length publishing. Image generation remains an agent capability; Comic Sol owns orchestration and validation, not credentials. Visual consistency is reinforced and audited, not guaranteed as pixel identity. Semantic work is authored by the agent into strict artifacts; deterministic scripts never call models. A project with unresolved error-level panels is blocked rather than partially exported. The happy path prioritizes original manga/anime direction, one bundled typeface, left-to-right reading, raster pages, and a transparent QA trail.

These constraints preserve a coherent end-to-end experience that a solo developer can implement and verify in three days while leaving visibly useful stretch directions after the submission is stable.
