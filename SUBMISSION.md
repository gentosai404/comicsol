# Comic Sol — OpenAI Build Week 2026 Submission Pack

## Project title

Comic Sol

## Track

Developer Tools

## Tagline

Turn one prompt or story file into an editable, QA-reviewed manga comic and deterministic PDF from Codex.

## Short description

Comic Sol is an installable Codex Skill that turns a short prompt, pasted story, or local `.txt`/`.md` file into a complete manga/anime comic project. Codex handles creative planning, image-capability orchestration, and visual review. Portable Python tools handle strict schemas, resumable state, deterministic dialogue lettering, panel composition, PDF export, integrity hashes, and transparent QA. Users keep editable storyboards, prompts, panel PNGs, page PNGs, a PDF, a manifest, and a human-readable report instead of receiving one opaque image.

## What it does

- Accepts one natural-language prompt, pasted narrative, or local story file.
- Plans 1–4 pages and up to 12 panels with character/scene continuity.
- Detects image-generation capability without embedding provider credentials.
- Generates and reviews canonical references and clean panel art.
- Keeps dialogue/captions deterministic and separates image-model SFX.
- Repairs only failed panels, then resumes downstream stages safely.
- Composes exact 1600×2400 pages and publishes a PDF atomically.
- Preserves editable artifacts, integrity hashes, cache state, and QA evidence.

## How Codex and GPT-5.6 Sol were used

Codex with GPT-5.6 Sol was primary builder and integration environment. It converted the product brief into the skill contract and implementation plan, developed the pipeline through TDD, diagnosed cross-platform edge cases, reviewed and integrated supporting audit findings, and drove live acceptance. Key decisions included keeping Comic Sol as a backend-only skill, separating agent judgment from deterministic rendering, preserving strict schema/atomicity guarantees, using progressive generation plus downstream-only invalidation, and adding byte-identical lettering/composition/PDF verification. The final Codex `/feedback` Thread ID is `019f7392-22ba-73f0-aa71-2d4a9cc1fdce`.

## Why it matters

Creative image workflows usually fail in the space between a prompt and a finished deliverable: continuity drifts, text is malformed, one bad panel forces a full restart, and users cannot inspect what happened. Comic Sol makes that workflow durable. A writer can revise plans and prompts, regenerate one panel instead of everything, inspect QA decisions, resume interrupted work, and publish consistent pages without a web app, paid build service, or provider-specific integration.

## Public repository

https://github.com/wenn-id/comic-sol

## Installation

```bash
git clone https://github.com/wenn-id/comic-sol.git \
  "${CODEX_HOME:-$HOME/.codex}/skills/comic-sol"
cd "${CODEX_HOME:-$HOME/.codex}/skills/comic-sol"
python3.11 -m pip install -r requirements.txt
```

## Judge test — no rebuild required

```bash
python3.11 scripts/comic_sol.py doctor
python3.11 -m unittest discover -s tests -v
python3.11 scripts/validate_project.py samples/sunlight-courier --stage final
python3.11 scripts/comic_sol.py resume-plan samples/sunlight-courier
```

Expected evidence:

- Doctor checks Python 3.11, Pillow 11.3.0, three bundled fonts, templates, and output access.
- Test suite: 137 tests pass on Linux/WSL; native Windows passes 137 with one privilege-dependent skip.
- Public sample validates at final stage.
- Resume plan reports six reusable stages and four reusable generated panels.

## Suggested live invocation

> Make a 2-page manga about a courier delivering sunlight to an underground city.

## Demo script — 1:49.13 rendered runtime

1. **0:00–0:12 — Problem and product**
   - Show repository and installed `comic-sol` skill.
   - Say: “Comic Sol turns one request into an editable, QA-reviewed comic project—not one opaque image.”
2. **0:12–0:28 — One invocation**
   - Enter the suggested prompt.
   - Show Codex selecting Comic Sol and the staged workflow.
3. **0:28–0:50 — Editable pipeline**
   - Open story plan, character bible, storyboard, and panel prompts.
   - Show reference routing and clean-panel files.
4. **0:50–1:13 — Deterministic finish**
   - Show dialogue lettering, composed 1600×2400 pages, PDF, manifest, and QA report.
   - Mention image-model SFX versus deterministic dialogue/captions.
5. **1:13–1:34 — Resume and repair**
   - Run `resume-plan` on `samples/sunlight-courier`.
   - Show all ten actions reusable; explain one failed panel can be regenerated without restarting.
6. **1:34–1:49 — Evidence and close**
   - Run `doctor` or show 137-test result.
   - Finish on the two-page PDF and public GitHub URL.

## Verified release evidence

- Linux/WSL Python 3.11: 137 tests passed.
- Native Windows 11 Python 3.11.9: 137 tests passed; one privilege-dependent symlink test skipped.
- Fresh virtualenv clean-room clone: 137 tests and doctor passed.
- Public sample: final validation passed; all 10 resume actions reusable.
- Two independent deterministic rerenders produced byte-identical hashes for four lettered panels, two page PNGs, and the PDF.
- Visual QA confirmed legible lettering, consistent borders/gutters, clean tail seams, and corrected speaker targeting.
- No embedded image-provider credentials; deterministic tools run offline.

## External-only submission fields

These cannot be completed from repository automation:

- [ ] Upload the rendered demo to YouTube as Public or Unlisted, then paste its URL into Devpost.
- [ ] Confirm final Devpost project profile and submit before the official deadline.
- [ ] Paste `/feedback` Thread ID: `019f7392-22ba-73f0-aa71-2d4a9cc1fdce`.
- [ ] Select **Developer Tools** track.
- [ ] Paste repository URL: https://github.com/wenn-id/comic-sol
- [ ] Verify YouTube playback while logged out.
- [ ] Verify Devpost submission confirmation/receipt.

## Submission checklist

- [x] Public repository
- [x] Install instructions
- [x] Judge test instructions without rebuild
- [x] README explains Codex/GPT-5.6 Sol collaboration
- [x] Real `/feedback` Thread ID recorded
- [x] Demo runtime under three minutes
- [x] Working sample and downloadable PDF committed
- [x] License and bundled-font licenses documented
- [x] Linux/WSL, native Windows, and clean-room verification
- [ ] YouTube URL entered
- [ ] Final Devpost submission confirmed

## Support / limitations summary

Comic Sol supports Python 3.11 plus Pillow 11.3.0 on Linux, macOS, Windows, and WSL. Deterministic scripts require no network access. New image creation requires an image-generation capability exposed by the active agent session. Results remain subject to external provider policies and image-model variability. CJK glyph coverage can fall back to boxes with bundled fonts; original art direction avoids named living artists, active studios, and franchise imitation.
