# Speaker-Aware Balloon Tails Design

**Date:** 2026-07-30

**Status:** Implemented and visually verified

**Target:** Comic Sol `v2.0.0rc4` prerelease

## Problem

RC2 dogfood produced readable lettering but visually incorrect speech-balloon tails:

- a device line pointed toward a human or empty space;
- human dialogue could terminate near a forehead or shoulder instead of the voice source;
- a short triangular wedge made the speaker ambiguous;
- page QA accepted approximate direction without proving the tail endpoint and speaker matched.

The current storyboard contract stores only `tail_target: [x, y]`. That coordinate has no semantic relationship to `speaker`, no voice-source type, and no protected endpoint around a face. The renderer then clamps the target into a short triangular polygon. The data can therefore be numerically valid while the rendered result is narratively wrong.

## Goals

1. Make the intended voice source explicit and machine-validatable.
2. Render a smooth, tapered, print-comic tail that joins the balloon body without a notch or doubled outline.
3. Keep the tail short enough not to cross faces or focal action while still clearly indicating the speaker.
4. Prevent system status and non-spoken device output from receiving speech tails.
5. Bind rendered tail geometry to deterministic provenance and stale-output validation.
6. Make page QA fail closed when speaker attribution or tail attachment is ambiguous.
7. Preserve project readability and deterministic, local-only operation without adding a model, network call, or dependency.

## Non-goals

- Face or mouth detection.
- Automatic inference of a speaker from image pixels.
- Changes to image-generation providers or the exact 17-tool MCP surface.
- Rewriting authored dialogue or changing balloon placement automatically.
- Claiming that geometry tests alone prove visual quality.

## Storyboard contract

### Dialogue text item

A newly authored dialogue item contains:

```json
{
  "id": "p01-02-t01",
  "kind": "dialogue",
  "speaker": "raka",
  "voice_source": "human",
  "speaker_anchor": [0.31, 0.27],
  "content": "Kalau begitu... aku ubah aturannya!",
  "anchor": "top-right",
  "priority": 1
}
```

Rules:

- `speaker` remains an entity ID present in both the character bible and the panel. A
  speaking drone/device is represented as a character-bible entity; the renderer never
  accepts an unbound free-form source name.
- `voice_source` is required and is one of `human` or `device`.
- `speaker_anchor` is required and contains two finite normalized coordinates in `[0, 1]`.
- For `human`, the anchor identifies the visible voice-source region near the mouth/face, not the character centroid, forehead, shoulder, hand, or arbitrary empty space.
- For spoken `device` dialogue, the anchor identifies the visible audio/source region of that device. Device status text that is not spoken uses a caption instead.
- Legacy `tail_target` remains readable for inspection and migration but is not accepted for new lettering or advancement. It is migrated explicitly to `speaker_anchor`; it is never silently reinterpreted.

### Caption and SFX

- `caption` and `sfx` keep `speaker: null`.
- They have neither `voice_source` nor `speaker_anchor`.
- System state such as `RC2: MODE AMAN.` is a caption and has no tail.
- SFX remains image-model-authored artwork and is not drawn by Pillow.

### Migration behavior

- Legacy storyboard data remains readable and produces a stable `balloon-tail-migration-required` validation issue at lettering and later stages.
- Planning/storyboard inspection can report the issue without corrupting or rewriting source data.
- A migration updates the semantic item, invalidates lettering and every downstream artifact, and preserves raw/clean panel images when dialogue content and generated SFX are unchanged.
- No migration guesses whether an old device line was spoken dialogue or a system caption; that decision must be explicit.

## Validation

Validation occurs before rendering and advancement.

For every dialogue item:

1. `speaker`, `voice_source`, and `speaker_anchor` are present and schema-valid.
2. The speaker exists in the character bible and appears in the panel.
3. The anchor lies inside the panel and outside the final fitted balloon ellipse plus an outline-safe margin.
4. The ray from balloon center to anchor intersects the ellipse exactly once in the outward direction.
5. The visible tail length after clamping is at least the minimum readable length and no more than the panel-relative maximum.
6. The tail tip remains inside the panel and stops before the authored anchor, leaving a protected gap around the voice source.
7. Caption/SFX items reject dialogue-only fields.

The engine does not claim that an authored human anchor is anatomically correct from coordinates alone. That judgment remains a required visual-QA check.

## Organic tail geometry

The renderer replaces the triangular polygon with a closed cubic path represented by two tapered sides:

- **Attachment:** the nearest point on the fitted ellipse along the ray toward `speaker_anchor`; this remains the semantic ray origin in provenance.
- **Base pair:** two points begin slightly inside the balloon body on opposite sides of the ray, so the merged mask—not a forced outline endpoint—forms the visible body-tail junction without a notch or doubled edge.
- **Tip:** a point on the attachment-to-anchor ray that stops before the anchor by a protected source gap.
- **Control points:** preserve each side of the ray, retain a durable white core, and converge without crossing or producing a needle-like section.

Deterministic constraints:

- geometry uses only storyboard coordinates, fitted balloon bounds, and panel dimensions;
- tail length is clamped by balloon minor radius and panel size;
- base width scales with balloon outline and is narrower than the existing wedge;
- source gap scales with panel size and prevents the tail from touching a face/device source;
- control points are finite, remain within panel bounds, and produce a non-self-intersecting silhouette;
- the supersampled body and tail are rasterized into one mask before a single outline is derived, preventing seams and doubled edges;
- no random values, computer vision, or platform-specific drawing primitives are used.

The public geometry helper returns a semantic record rather than an opaque tuple. The record includes:

- `voice_source`;
- normalized `speaker_anchor`;
- pixel `attachment`, `base`, `control`, and `tip` points;
- source-gap, length, and width measurements;
- renderer policy version.

## Provenance and invalidation

Lettering geometry provenance records the new semantic fields and complete resolved geometry. Its canonical hash changes when any of these change:

- speaker;
- voice source;
- speaker anchor;
- balloon placement or fitted bounds;
- panel dimensions;
- font/text geometry;
- renderer policy version.

A mismatch makes lettering, composition, page QA, PDF verification, and report output stale. Raw and clean panel art remain reusable unless generated SFX or panel-generation inputs changed.

## Page QA

The page-QA evidence contract must make attribution explicit for each dialogue item.
The existing schema-2.0 `bubble-tail-direction` check retains its bounded evidence
shape; its `regions` array contains exactly one structured entry per rendered dialogue
item. Each entry records:

- `panel_id` and `text_id`;
- declared `speaker` and `voice_source`;
- current normalized `speaker_anchor`;
- current resolved pixel `tip` from lettering geometry;
- reviewer `result`, which must agree with the enclosing check result.

The reviewer evidence text remains responsible for confirming that the endpoint clearly indicates the declared source, avoids faces/text/focal action, and has a continuous body-tail join and outline. Deterministic fields bind that visual judgment to the current rendered dialogue; they do not infer a visual pass.

A page cannot be marked reviewed when any dialogue tail:

- points to the wrong speaker or empty space;
- ends at an implausible human region such as a forehead or shoulder;
- is detached, self-crossing, needle-like, wedge-like, or visibly notched;
- touches a face/source instead of stopping before it;
- is ambiguous between multiple possible speakers.

The deterministic lettering geometry supplies the expected item IDs and endpoints, so
the reviewer cannot omit a dialogue item or invent an extra one. System captions are
checked for having no tail. Deterministic checks prove geometry mechanics; retained
visual evidence is still required for a visual-quality claim.

## Error handling and transactions

- Invalid semantics or geometry fail before publication with stable categories.
- Lettering remains transactional: no partial panel, geometry record, cache, or manifest update is retained on failure.
- A failed re-letter operation preserves the last valid panel and provenance.
- Resume reuses upstream artifacts only when their semantic hashes remain current.

## Testing strategy

### RED contracts

Tests first reproduce the four RC2 failure classes:

1. device/status text attributed toward a human or empty space;
2. human tail endpoint at a forehead/shoulder rather than the authored voice-source anchor;
3. ambiguous short wedge that cannot establish a speaker;
4. body-tail notch or doubled outline.

### Deterministic tests

- schema acceptance/rejection and legacy migration gate;
- ellipse intersection, source gap, clamping, finite control points, bounds, and no self-intersection;
- renderer produces a connected silhouette with one continuous outline;
- geometry hash changes for every semantic input;
- transactional rollback and stale downstream validation;
- caption/system text has no tail;
- cross-platform byte determinism where the existing rendering contract requires it.

### Visual acceptance

A retained local fixture renders representative human and device cases at production panel sizes. Acceptance requires side-by-side inspection showing:

- correct speaker attribution;
- smooth body attachment;
- compact, tapered shape;
- consistent outline thickness;
- protected face/source gap;
- no text, face, or focal-action obstruction.

The final report must distinguish deterministic mechanics evidence from visual review evidence.

## Compatibility and release

- Canonical engine remains under `scripts/*.py`; changed runtime files remain required wheel members.
- No new dependency, provider, network call, GUI, or MCP tool is introduced.
- Exact MCP surface remains 17 tools.
- Existing RC3 tags and artifacts remain immutable.
- Delivery uses a feature branch, focused and full regression, build/distribution proof, visual fixture evidence, PR, cross-platform CI, merge, and a new prerelease only after merged-commit verification.

## Acceptance criteria

The change is complete only when:

1. legacy free-coordinate tails fail with the stable migration gate;
2. new dialogue cannot render without explicit speaker semantics;
3. system captions render without tails;
4. organic curve geometry passes deterministic invariants and provenance checks;
5. actual rendered fixtures pass documented visual inspection;
6. the four RC2 failure classes are covered by regression tests;
7. full tests, build, distribution validation, clean-install base/MCP, and exact 17-tool smoke pass;
8. cross-platform CI passes before merge and release.
