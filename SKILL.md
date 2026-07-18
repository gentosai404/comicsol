---
name: comic-sol
description: Create, storyboard, render, resume, repair, and export finished original manga/anime comics from a short prompt, prose story, pasted narrative, or local .txt/.md source. Use when Codex should produce editable plans, consistent panel PNGs, composed page PNGs, a PDF, manifest, and transparent QA report without building a web app.
---

# Comic Sol

Turn one natural-language request into a local, editable comic project. Operate as an
agent workflow: reason about story and images, use an exposed image-generation
capability, and delegate deterministic validation, lettering, composition, export, and
reporting to the bundled Python scripts.

## Read progressively

- Read [workflow](references/workflow.md) for input detection, all ten stages, commands,
  state transitions, failures, resume, and completion.
- Read [creative direction](references/creative-direction.md) before authoring plans,
  character fingerprints, storyboards, references, or image prompts.
- Read [capability detection](references/capability-detection.md) immediately before
  selecting or invoking an image-generation tool.
- Read [visual QA](references/visual-qa.md) before accepting, retrying, overriding,
  composing, or exporting any generated panel.
- Read [safety and IP](references/safety-ip.md) before sending prompts externally and
  whenever people, minors, sensitive data, named styles, franchises, or refusals appear.
- Read [schemas](references/schemas.md) whenever writing or revising JSON artifacts.

## Core orchestration

1. Detect resume/source-file/pasted-story/short-prompt mode in the normative order.
2. Ask only a materially required question listed in the workflow reference; otherwise
   apply defaults and continue without confirmation.
3. Run the local doctor, initialize or inspect the project, then write and validate each
   semantic artifact before advancing its status.
4. Detect image capability from tools exposed in the current agent session. Do not ask
   deterministic scripts to discover or call an image provider.
5. Generate canonical references and panels into attempt paths, inspect them visually,
   record all seven QA checks, and selectively repair only failures within budget.
6. Promote accepted attempts, letter panels, compose pages, export PDF, render the QA
   report, validate final integrity, and transition to the honest terminal status.
7. Return status, counts, warnings, and clickable project output paths.

## Deterministic command route

Use Python 3.11 from the skill root. Replace uppercase placeholders with resolved paths
or values; quote shell arguments safely.

```text
python3.11 scripts/comic_sol.py doctor --output-root OUTPUT_ROOT
python3.11 scripts/comic_sol.py init --output-root OUTPUT_ROOT --title TITLE --source SOURCE --request-json REQUEST_JSON
python3.11 scripts/comic_sol.py status PROJECT_DIR --json
python3.11 scripts/comic_sol.py transition PROJECT_DIR TARGET [--warning TEXT]
python3.11 scripts/validate_project.py PROJECT_DIR --stage plan|storyboard|panels|final [--json]

python3.11 scripts/comic_sol.py resume-plan PROJECT_DIR --json
python3.11 scripts/comic_sol.py invalidate PROJECT_DIR STAGE
python3.11 scripts/comic_sol.py record-attempt PROJECT_DIR PANEL_ID initial|visual_retry|transient_repeat PATH
python3.11 scripts/comic_sol.py promote-attempt PROJECT_DIR PANEL_ID PATH
python3.11 scripts/comic_sol.py override-panel PROJECT_DIR PANEL_ID --reason TEXT

python3.11 scripts/letter_panels.py PANEL_DIR --output-root PATH [--font PATH]
python3.11 scripts/compose_pages.py PROJECT_DIR --all
python3.11 scripts/compose_pages.py PROJECT_DIR --page N
python3.11 scripts/export_pdf.py PROJECT_DIR [--output PATH]
python3.11 scripts/render_report.py PROJECT_DIR [--output PATH]
```

Never fabricate successful artifacts, provider capability, visual evidence, or a terminal
success status. Preserve editable intermediates and stop at `BLOCKED` when safe completion
is impossible.
