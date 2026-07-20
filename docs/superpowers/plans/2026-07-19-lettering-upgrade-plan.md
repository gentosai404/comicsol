# Lettering Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers/subagent-driven-development (recommended) or superpowers/executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade lettering to a Manga Shōnen direction via a hybrid model: dialogue and minimal captions rendered deterministically in Pillow, and SFX rendered dynamically by the image model in the artwork.
**Architecture:** Update `letter_panels.py` to draw organic oval balloons, polygon tails, and parse `**emphasis**`. Exclude `sfx` from Pillow rendering. Update agent instructions and validators to enforce this split.
**Tech Stack:** Python 3.11, Pillow 11.3.0, JSON schemas.

## Global Constraints

- No external dependencies beyond Pillow 11.3.0 and the Python 3.11 standard library.
- Deterministic hashing for artifacts.
- Graceful Unicode fallback using NotoSans.
- Test-Driven Development: write failing tests first.
- Frequent commits.
- Exact file paths and expected commands.

---

### Task 1: Integrate Comic Display Font

**Files:**
- Create: `assets/fonts/ComicNeue-Regular.ttf`
- Create: `assets/fonts/ComicNeue-Bold.ttf`
- Modify: `scripts/comic_sol.py:24-24`, `scripts/comic_sol.py:895-897`
- Modify: `scripts/letter_panels.py:20-20`
- Test: `tests/test_manifest.py:231-236`

**Interfaces:**
- Consumes: N/A
- Produces: `FONT_PATH_COMIC_REGULAR`, `FONT_PATH_COMIC_BOLD` global paths, and doctor font checks.

- [ ] **Step 1: Download Comic Neue fonts into assets**

```bash
curl -fsSL https://raw.githubusercontent.com/google/fonts/main/ofl/comicneue/ComicNeue-Regular.ttf -o assets/fonts/ComicNeue-Regular.ttf
curl -fsSL https://raw.githubusercontent.com/google/fonts/main/ofl/comicneue/ComicNeue-Bold.ttf -o assets/fonts/ComicNeue-Bold.ttf
```

- [ ] **Step 2: Update `comic_sol.py` doctor to load the new font**

Modify `scripts/comic_sol.py` to check `ComicNeue-Regular.ttf`:

```python
FONT_PATH = ROOT / "assets/fonts/ComicNeue-Regular.ttf"
```

- [ ] **Step 3: Run doctor test to verify PASS**

Run: `python3.11 -m unittest tests.test_manifest.OfflineTests.test_doctor_checks_local_runtime_and_defers_image_capability -v`
*(Note: adjust test path to match your local run if necessary, or run `python3.11 scripts/comic_sol.py doctor --output-root /tmp/comic` to verify).*

- [ ] **Step 4: Update `letter_panels.py` globals**

Modify `scripts/letter_panels.py` to export the new fonts:

```python
FONT_PATH = ROOT / "assets/fonts/ComicNeue-Regular.ttf"
FONT_PATH_BOLD = ROOT / "assets/fonts/ComicNeue-Bold.ttf"
FONT_PATH_FALLBACK = ROOT / "assets/fonts/NotoSans-Regular.ttf"
```

Modify the CLI defaults in `_build_parser` to use `FONT_PATH`.

- [ ] **Step 5: Commit**

```bash
git add assets/fonts/ComicNeue-*.ttf scripts/comic_sol.py scripts/letter_panels.py
git commit -m "feat: integrate Comic Neue display fonts"
```

---

### Task 2: Implement Emphasis Parser and Font Fallback

**Files:**
- Modify: `scripts/letter_panels.py`
- Test: `tests/test_lettering.py`

**Interfaces:**
- Consumes: `FONT_PATH`, `FONT_PATH_BOLD`, `FONT_PATH_FALLBACK`
- Produces: `_parse_emphasis(text: str) -> list[tuple[str, bool]]` (returns chunks of text and whether they are bold).
- Produces: `_load_font(size: int, bold: bool)` handling fallback gracefully.

- [ ] **Step 1: Write failing tests**

In `tests/test_lettering.py`, add:

```python
    def test_emphasis_parsing(self):
        from letter_panels import _parse_emphasis
        self.assertEqual([("Hello ", False), ("world", True), ("!", False)], _parse_emphasis("Hello **world**!"))
        self.assertEqual([("Literal ** missing", False)], _parse_emphasis("Literal ** missing"))
        self.assertEqual([("bold", True)], _parse_emphasis("**bold**"))
        self.assertEqual([("mixed **stars", False)], _parse_emphasis("mixed **stars"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3.11 -m unittest tests.test_lettering.LetteringTests.test_emphasis_parsing -v`
Expected: FAIL with ImportError.

- [ ] **Step 3: Write minimal implementation**

In `scripts/letter_panels.py`, add:

```python
def _parse_emphasis(text: str) -> list[tuple[str, bool]]:
    """Parse **bold** markdown into (text, is_bold) chunks."""
    chunks = []
    parts = text.split("**")
    if len(parts) % 2 == 0:
        return [(text, False)]
    for i, part in enumerate(parts):
        if part:
            chunks.append((part, i % 2 != 0))
    return chunks

def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_PATH_BOLD if bold else FONT_PATH
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        return ImageFont.truetype(str(FONT_PATH_FALLBACK), size)
``` (Note: Implement fallback per-character or per-chunk when glyph is missing, since ComicNeue lacks Cyrillic/Greek/Emoji.)

- [ ] **Step 4: Run test to verify it passes**

Run: `python3.11 -m unittest tests.test_lettering.LetteringTests.test_emphasis_parsing -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/letter_panels.py tests/test_lettering.py
git commit -m "feat: parse emphasis and manage bold fonts"
```

---

### Task 3: Manga Shōnen Dialog Balloons and Tails

**Files:**
- Modify: `scripts/letter_panels.py`
- Modify: `tests/test_lettering.py`

**Interfaces:**
- Consumes: text rectangles.
- Produces: Oval balloons drawn via `Drawing.pieslice` or `polygon` approximations, with triangular tails pointing to the `tail_target`.

- [ ] **Step 1: Update the dialogue test for oval/polygon geometry**

Modify `test_dialogue_has_white_box_dark_stroke_and_tail` in `tests/test_lettering.py` to `test_dialogue_has_oval_balloon_and_polygon_tail`. Update assertions to expect oval bounds and polygon lines pointing to `[0.75, 0.7]` (scaled to image size).
- [ ] **Step 2: Run test to verify failure**

Run: `python3.11 -m unittest tests.test_lettering.LetteringTests.test_dialogue_has_oval_balloon_and_polygon_tail -v`

- [ ] **Step 3: Implement organic balloons and tails**

In `scripts/letter_panels.py`, update `render_text_item`:

```python
    if kind == "dialogue":
        tail = item.get("tail_target")
        # Draw tail
        if isinstance(tail, list) and len(tail) == 2 and all(isinstance(value, (int, float)) for value in tail):
            target_x = min(image_width - 1, max(0, round(float(tail[0]) * image_width)))
            target_y = min(image_height - 1, max(0, round(float(tail[1]) * image_height)))
            center_x = (x0 + x1) // 2
            center_y = (y0 + y1) // 2
            
            # Simple polygon tail
            tail_width = max(16, (x1 - x0) // 6)
            draw.polygon(
                [(center_x - tail_width//2, center_y),
                 (center_x + tail_width//2, center_y),
                 (target_x, target_y)],
                fill=(255, 255, 255, 255),
                outline=(15, 15, 15, 255),
                width=3
            )
        
        # Draw oval balloon
        draw.ellipse(
            (x0, y0, x1, y1),
            fill=(255, 255, 255, 255),
            outline=(15, 15, 15, 255),
            width=3
        )
        
        # Render text with emphasis support
        # (Replace the single multiline_text call with a chunked renderer, or 
        # strip ** for metric bounds and draw standard text for MVP if chunking is too complex for one step.
        # For this design, drawing stripped text is acceptable if exact kerning fails, but try to support it).
        clean_text = content.replace("**", "")
        draw.multiline_text((text_x, text_y), clean_text, font=font, fill=(10, 10, 10, 255), spacing=6, align="center")
```
*Note for implementer: if inline bold rendering proves computationally complex within Pillow, rendering the stripped text using the bold font when emphasis is present anywhere in the string is an acceptable degradation.*

- [ ] **Step 4: Run test to verify it passes**

Run: `python3.11 -m unittest tests.test_lettering.LetteringTests.test_dialogue_has_oval_balloon_and_polygon_tail -v`

- [ ] **Step 5: Commit**

```bash
git add scripts/letter_panels.py tests/test_lettering.py
git commit -m "feat: draw manga oval balloons and tails"
```

---

### Task 4: Minimal Captions and Skipping SFX

**Files:**
- Modify: `scripts/letter_panels.py`
- Modify: `tests/test_lettering.py`

**Interfaces:**
- Consumes: text item kind.
- Produces: Minimal captions (no large black boxes) and no rendering for `sfx`.

- [ ] **Step 1: Write failing tests**

In `tests/test_lettering.py`, add a test to verify SFX is skipped:
```python
    def test_sfx_is_skipped_by_lettering(self):
        first = self.panel.read_bytes()
        letter_panel(str(self.panel), 800, 1000, [sfx()], self.characters)
        self.assertEqual(first, self.panel.read_bytes())
Remove `test_sfx_is_deterministic_and_impact_styled`.
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3.11 -m unittest tests.test_lettering.LetteringTests.test_sfx_is_skipped_by_lettering -v`

- [ ] **Step 3: Write minimal implementation**

In `scripts/letter_panels.py`, update `render_text_item` and `_item_font_and_lines` to skip `sfx`:

```python
    if kind == "sfx":
        return # Skip SFX entirely, handled by image model
```

Update the `caption` block in `render_text_item`:
```python
    elif kind == "caption":
        # Minimal strip
        draw.rectangle(
            (x0, y0, x1, y1),
            fill=(255, 255, 255, 230),
            outline=(15, 15, 15, 255),
            width=2,
        )
        clean_text = content.replace("**", "")
        draw.multiline_text((text_x, text_y), clean_text, font=font, fill=(15, 15, 15, 255), spacing=6, align="center")
```

- [ ] **Step 4: Run tests**

Run: `python3.11 -m unittest discover -s tests -v`
Fix any failing layout tests that expected the old caption/sfx bounds.

- [ ] **Step 5: Commit**

```bash
git add scripts/letter_panels.py tests/test_lettering.py
git commit -m "feat: render minimal captions and skip SFX"
```

---

### Task 5: Update Agent Instructions for SFX

**Files:**
- Modify: `SKILL.md`
- Modify: `references/creative-direction.md`
- Modify: `references/visual-qa.md`
**Interfaces:**
- Consumes: Agent rules.
- Produces: Explicit instructions to push SFX into the image prompt.

- [ ] **Step 1: Write the failing check**

Run: `python3.11 -m unittest tests.test_validation.SkillContractTests.test_visual_qa_budgets_checks_and_completion_contract -v`
Modify `tests/test_validation.py` if necessary to assert the new SFX rules exist in the documentation.

- [ ] **Step 2: Implement the rule changes**

In `references/creative-direction.md`, append to the prompt construction rules:
```markdown
8. Onomatopoeia (SFX): Instruct the model to draw the SFX text directly into the artwork using dynamic motion typography. Never ask for dialogue or captions to be drawn.
```

In `SKILL.md` and `references/visual-qa.md`, change rule 6/text-free from "no generated lettering, bubble, caption" to "no generated dialogue, bubble, or caption. SFX must be drawn in the art."

- [ ] **Step 3: Run full regression**

Run: `python3.11 -m unittest discover -s tests -v`
Run: `python3.11 scripts/comic_sol.py doctor --output-root /tmp/comic-doctor`

- [ ] **Step 4: Commit**

```bash
git add SKILL.md references/creative-direction.md references/visual-qa.md tests/test_validation.py
git commit -m "docs: instruct agent to generate SFX via image prompts and update visual QA"
```
