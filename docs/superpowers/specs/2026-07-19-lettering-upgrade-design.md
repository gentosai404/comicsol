# Comic Sol Lettering Upgrade Design

**Topic:** Lettering Upgrade (Manga Shōnen Direction)
**Date:** 2026-07-19

## 1. Problem and Intent
The current deterministic lettering engine (Pillow) produces generic, rigid text: uniform bold-free sans-serif, rounded rectangle balloons, large black captions, and visually disconnected SFX. The fix must elevate the output to feel like professional manga/anime without abandoning the deterministic pipeline (i.e. not building a full UI editor or complex engine) and without compromising existing guarantees like deterministic hashing and robust error handling.

The user's approved priority is: **Quality over speed**, specifically **Manga shōnen style** with a **Hybrid rendering approach**.

## 2. Solution: Hybrid Manga Shōnen Lettering

### Core Split
1. **Dialogue & Captions:** Handled deterministically by `letter_panels.py` (zero-typo guarantee).
2. **SFX (Onomatopoeia):** Excluded from Pillow, injected directly into the visual prompt to be drawn by the image model as part of the artwork.

### Visual Components (Manga Shōnen)
- **Dialogue Font:** A natural comic font (e.g. `Comic Shanns`, `Kalam`, or `Gaegu`) for dialogue, with `NotoSans` retained strictly as a fallback for missing Unicode glyphs.
- **Balloons:** Organic capsule/oval shape (`Drawing.arc` / `pieslice`) replacing `rounded_rectangle`. Pure white fill, sharp black outline.
- **Tails:** A solid triangle/polygon connecting the balloon seamlessly to the speaker's `tail_target` coordinate, rather than a standalone stroke line.
- **Emphasis:** A lightweight markup parser for `**bold**` words within dialogue, rendered inline with a larger size or stroke.
- **Captions:** Replaced from large black rounded rectangles to minimal, elegant floating strips (or translucent overlays).
- **SFX Prompting:** The `sfx` kind is no longer lettered by Pillow. Instead, `STORYBOARDED` templates and image prompts must explicitly instruct the model to draw the exact SFX word with motion/action styles.

## 3. Architecture and File Changes

### 1. `scripts/letter_panels.py`
- Modify `_item_font_and_lines` to use the new primary comic font and detect `**emphasis**`.
- Modify `render_text_item` branch `dialogue`: draw an oval balloon and a polygon tail pointing to `tail_target`.
- Modify `render_text_item` branch `caption`: simplify the background box.
- Modify `render_text_item` branch `sfx`: skip entirely (no-op).

### 2. Assets
- Add a free/libre comic font (e.g. `ComicShanns.ttf` or `Kalam.ttf`) to `assets/fonts/`.
- Maintain `NotoSans-Regular.ttf` as a fallback.

### 3. Agent Prompts / Templates
- Update `SKILL.md` or prompt instructions to clarify that SFX must be handled by the image generator.
- Update `validate_project.py` if needed to ensure `sfx` text items remain valid in schema but are treated as metadata/prompts rather than strict Pillow text elements.

### 4. QA and Tests
- `tests/test_lettering.py`:
  - Update `test_dialogue_has_white_box_dark_stroke_and_tail` to expect oval/polygon tail geometry.
  - Update or remove `test_sfx_is_deterministic_and_impact_styled` since SFX is skipped.
  - Add tests for emphasis parsing.

## 4. Error Handling
- **Font Load Failure:** Graceful fallback to `NotoSans`.
- **Emphasis Parse Failure:** Render literal `**` characters, never drop text.
- **SFX Missed by Model:** The existing visual QA loop (which checks for SFX presence visually) remains unchanged. If the model fails, it burns a retry budget. If it fails repeatedly, the panel is `BLOCKED`.

## 5. Scope Boundaries
- **No new schema:** The `text_items` JSON schema remains identical.
- **No GUI editor:** Lettering remains a headless backend pass.
- **No external dependencies:** Python standard library + Pillow only.

## 6. Review Checklist
- [x] Clear division between deterministic text and model text? Yes.
- [x] Style aligns with user request? Yes, Manga shōnen.
- [x] Retains deterministic hash guarantees for unmodified outputs? Yes.
- [x] Respects existing test suite boundary? Yes, tests will be adapted.
