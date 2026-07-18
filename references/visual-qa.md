# Visual QA

Inspect every generated raw panel against its storyboard, character/scene references, and
declared invariants. Record non-empty evidence for exactly seven ordered checks:

1. `character-identity`: principal identity and all visible fingerprint invariants.
2. `anatomy`: readable pose, hands, limbs, face, and no beat-breaking defects.
3. `action`: the scripted action and important props are present and correct.
4. `composition`: camera, subject placement, focus, and reserved text-safe area work.
5. `continuity`: exact character and scene anchors match adjacent panels.
6. `text-free`: no generated lettering, bubble, caption, logo, signature, or watermark.
7. `technical`: readable raster, minimum 512 px dimensions, aspect within ±2%, and no
   unintended alpha.

Results are `pass`, `warning`, or `fail`; severity is `warning` or `error`. Decisions are:

- `accept`: all required checks pass.
- `accept_with_warnings`: readable warning-level impact remains and is named for the user.
- `regenerate`: an error-level failure needs a new attempt.

## Selective repair budgets

- Initial generation permits at most 2 regenerations per panel.
- Visual retries and transient repeats share 8 extra calls project-wide.
- A retry appends exactly one correction clause for observed failures while preserving
  every canonical anchor, reference, and other prompt content.
- Retain all attempt images. Do not touch passing panels or their hashes.
- Permit one immediate transient repeat; it consumes the global budget but not the
  per-panel visual retry budget.
- After exhaustion, an error-level panel is `BLOCKED` and cannot reach lettering/export.

An explicit user may override a non-safety visual error with a recorded reason, producing
`COMPLETE_WITH_WARNINGS`. Never override an unreadable/corrupt image or safety refusal.

## Composed-page QA

After composition, inspect numeric order, page continuity, borders/gutters, clipped or
overlapping text, bubble/caption readability, tail direction, covered faces/actions, and
consistent reading flow. Any error-level panel or page keeps export blocked. Deterministic
hash/dimension/PDF checks complement visual inspection; they do not replace it.
