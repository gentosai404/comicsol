# Comic Sol Lab v2 Maturity Design

**Date:** 2026-07-23

**Status:** Approved design; Integrity Core implementation plan complete

**Repository:** `wenn-id/comic-sol-lab` (private)

**Development branch:** `ai/post-event-development`

## 1. Purpose

Comic Sol Lab v2 turns the hackathon-era Codex Skill and deterministic comic pipeline into a mature open-source Skill/MCP product that anyone can install and use without managing Python, virtual environments, repository paths, or client configuration manually.

The product remains a local-first CLI, Skill, and MCP system. It does not become a hosted service or GUI application.

## 2. Product goal

A new user on Windows, macOS, Linux, WSL, or a container can:

1. install Comic Sol using a native installer;
2. have supported agent clients detected and configured safely;
3. create a comic through the Skill, CLI, or MCP;
4. recover from interruption or temporary capability failure;
5. produce a validated PDF with trustworthy QA and provenance;
6. upgrade or uninstall without losing comic projects.

## 3. Success criteria

Comic Sol Lab v2 is release-ready only when all of the following are demonstrated on clean environments:

- No system Python installation is required.
- `comic-sol doctor` passes after installation.
- Supported clients are configured idempotently with backup and rollback.
- MCP protocol discovery and a complete deterministic lifecycle pass.
- A sample project reaches `COMPLETE` only with current panel QA, lettered panels, page QA, pages, report, and PDF.
- An interrupted project resumes without manual manifest editing.
- Concurrent clients cannot exceed retry budgets or corrupt project state.
- Installer upgrade preserves projects and configuration.
- Uninstall removes product integration but preserves user projects by default.
- Linux, macOS, Windows native, WSL, and container gates are green.

## 4. Scope

### 4.1 Included

- Portable Python package and bundled runtime.
- Stable `comic-sol` CLI.
- Codex-compatible Skill distribution.
- Full deterministic MCP lifecycle.
- Agent-driven image generation by default.
- Optional provider adapters.
- Native installers for major desktop platforms.
- OCI container distribution.
- Safe client auto-configuration.
- Crash-safe project mutation and actionable resume.
- Fail-closed validation and finalization.
- Stronger panel, page, typography, and PDF QA.
- Cross-platform CI and clean-environment release testing.

### 4.2 Non-goals

- Hosted multi-user service.
- Web or desktop GUI.
- Accounts, billing, teams, or collaboration.
- Cloud storage or remote project database.
- Mandatory image-provider account.
- Automatic visual-similarity scores as hard quality gates.
- Microservices.
- Replacing creative agent reasoning with deterministic code.

## 5. Delivery strategy

Development is reliability-first and incremental. Existing behavior and 143-test baseline are retained where compatible. No rewrite is authorized.

Milestones:

1. **Integrity Core** — close correctness, security, concurrency, recovery, and validation gaps.
2. **Portable Product** — package stable CLI, complete MCP, provider and client contracts, cross-platform CI.
3. **Native Distribution** — bundled runtime and native/container installers.
4. **Comic Quality** — trustworthy QA provenance, page/PDF verification, typography, layouts, and sample matrix.

A milestone may not claim completion while any acceptance gate in that milestone is red.

## 6. Architecture

Comic Sol remains one Python codebase with bounded internal modules:

```text
comic-sol/
├── engine/       state, validation, locks, transactions, resume, artifacts
├── providers/    agent-driven contract and optional image adapters
├── clients/      supported client detection and safe configuration
├── mcp/          thin protocol adapter to engine operations
├── cli/          stable end-user command surface
├── skill/        creative reasoning and workflow instructions
├── installers/   native and container packaging assets
└── tests/        unit, integration, protocol, recovery, packaging, OS gates
```

This is a logical target layout, not permission for a mechanical directory rewrite. Files move only when required by implementation boundaries. Small, working diffs take priority over architectural cosmetics.

### 6.1 Single source of truth

Engine functions own all deterministic business rules. CLI, MCP, providers, client setup, and installers call engine interfaces. They must not duplicate state transitions, validation, retry accounting, artifact hashing, or path rules.

### 6.2 Compatibility

- Existing schema v1 projects remain readable.
- Schema migrations are explicit, tested, and reversible until new output is committed.
- Existing public submission repository remains frozen during judging.
- Private Lab changes do not modify `wenn-id/comic-sol/main`.

## 7. Stable CLI

The installed executable is:

```text
comic-sol
```

Required commands:

```text
comic-sol doctor
comic-sol init
comic-sol run
comic-sol status
comic-sol validate
comic-sol resume
comic-sol setup
comic-sol repair
comic-sol uninstall
comic-sol mcp
```

### 7.1 Command behavior

- Human output is concise and actionable.
- Machine consumers can request structured JSON.
- Errors use stable categories and non-zero exit codes.
- No command prints secrets, raw provider payloads, absolute private paths, or prompt content into persistent logs.
- Commands that mutate a project take the project lock.
- `resume` reports preserved artifacts and destructive effects before invalidation.
- `repair` handles interrupted transactions and damaged client integration; it does not silently rewrite authored story data.

## 8. State and recovery

The normal state order remains:

```text
INIT
PLANNED
SCRIPTED
STORYBOARDED
REFERENCES_READY
PANELS_READY
QA_READY
LETTERED
COMPOSED
EXPORTED
COMPLETE
```

### 8.1 BLOCKED state

`BLOCKED` is recoverable. Blocking metadata records:

- `blocked_from`: last normal state;
- `blocked_reason`: stable category;
- warning identity and creation time;
- required recovery condition.

`comic-sol resume`:

1. validates project structure;
2. determines last valid stage from artifact hashes and cache;
3. checks whether blocking condition is resolved;
4. restores the valid state;
5. retains valid artifacts;
6. removes only resolved blocking warnings;
7. runs deterministic stale stages when safe;
8. reports agent-required generation work when deterministic continuation is impossible.

Resume never requires manual manifest editing.

## 9. Trust-boundary validation

Shared engine boundaries enforce rules for CLI and MCP equally.

### 9.1 Source input

- Accepted source file types: UTF-8 `.txt` and `.md`.
- Maximum source size: 200 KiB measured as UTF-8 bytes.
- Unsupported encoding, extension, or size fails before project directory creation.
- Direct MCP `source_text` follows the same byte limit.

### 9.2 Paths

Every project-controlled artifact path:

- is relative to the project root;
- rejects absolute paths and `..` traversal;
- rejects sibling-prefix escapes;
- rejects symlink, junction, and reparse-point escape;
- is resolved and contained again immediately before read or write.

Composition, lettering, promotion, export, validation, CLI, and MCP use one containment implementation.

## 10. Concurrency, atomicity, and durability

### 10.1 Project lock

Every mutation uses a cross-process lock at:

```text
<project>/.comic-sol.lock
```

The implementation must support Windows, macOS, Linux, WSL, and container filesystems. Lock acquisition has a bounded timeout and returns owner/process diagnostics without exposing secrets.

### 10.2 Transaction journal

Multi-file operations use a journal:

```text
logs/transactions/<transaction-id>.json
```

Transaction sequence:

1. acquire project lock;
2. preflight all inputs and destinations;
3. write outputs into project-local staging;
4. flush and fsync files where supported;
5. publish all outputs;
6. fsync parent directories where supported;
7. update manifest, cache, and event log consistently;
8. remove journal;
9. release lock.

On startup or `repair`, incomplete transactions are deterministically completed or rolled back. A failed multi-page composition cannot leave mixed old/new pages.

### 10.3 Retry accounting

Per panel:

- exactly one initial attempt;
- at most one transient repeat;
- at most two visual retries;
- at most eight extra calls globally.

An attempt is counted only after it decodes as a supported raster and is at least 512×512. Counter validation, increment, retained artifact publication, and event logging happen under one lock. Concurrent processes cannot exceed limits or lose accounting.

## 11. Validation and finalization

Validation is fail-closed. Missing descriptors never imply success.

### 11.1 Required final artifacts

A terminal project requires current descriptors and matching hashes for:

- character bible;
- story plan;
- storyboard;
- raw and normalized clean panel files;
- panel QA records;
- lettered panel files;
- page QA records;
- composed page PNGs;
- QA report;
- exported PDF;
- stage cache entries.

### 11.2 Finalization order

```text
panel QA
→ lettering
→ composition
→ page QA
→ PDF export
→ decoded PDF verification
→ QA report
→ final validation
→ COMPLETE
```

Export does not imply completion. `COMPLETE` transition and `comic_finalize` fail without final validation. Failure must not replace a previously valid PDF or page set.

## 12. MCP contract

The MCP server runs through:

```text
comic-sol mcp
```

Clients do not reference a Python interpreter, virtual environment, checkout, or internal script.

Required tools:

```text
comic_doctor
comic_init
comic_status
comic_validate
comic_resume_plan
comic_resume
comic_transition
comic_invalidate
comic_record_stage
comic_record_attempt
comic_promote_attempt
comic_override_panel
comic_letter
comic_compose
comic_render_report
comic_export
comic_finalize
```

### 12.1 MCP guarantees

- Thin calls into engine functions.
- Structured success and stable error categories.
- Locked output root.
- No arbitrary filesystem or command execution.
- Sampling disabled unless a future spec explicitly enables it.
- CLI/MCP deterministic lifecycle parity.
- Protocol integration test starts at init and reaches a valid PDF, report, cache, and terminal state.

## 13. Generation providers

### 13.1 Default agent-driven mode

The Skill asks the host agent to use its available image tool. The agent stores the resulting file as a retained attempt through the same engine contract used by provider adapters.

### 13.2 Optional adapters

Initial adapter families:

1. OpenAI-compatible image API;
2. FAL-compatible API;
3. ComfyUI HTTP;
4. generic local command adapter.

Provider packages remain optional. Base deterministic functionality and tests work without them.

### 13.3 Provider-neutral records

`GenerationRequest`, `GenerationResult`, and `GenerationFailure` represent:

- provider and model/version when exposed;
- request ID when exposed;
- requested and actual dimensions;
- reference-image support and actual use;
- seed when exposed;
- attempt path and SHA-256;
- sanitized outcome category;
- sanitized provider error.

API keys are read from environment variables or OS credential stores. They never enter project files, event logs, reports, prompts, or exception output.

## 14. QA provenance

Each panel QA record binds the review to:

- raw and clean SHA-256;
- raw and clean dimensions;
- normalization mode and crop box;
- storyboard SHA-256;
- character-reference SHA-256 values;
- reviewer/method identity;
- review timestamp;
- check-specific observed evidence;
- generation provenance;
- attempt counters and retry reason.

The seven normative checks remain:

1. character identity;
2. anatomy;
3. action;
4. composition;
5. continuity;
6. text-free;
7. technical.

Identical placeholder evidence, including generic values such as `verified`, cannot satisfy all checks.

Automated visual similarity is advisory only until benchmarked false-positive and false-negative rates justify a separate specification.

## 15. Normalization and lettering

### 15.1 Image normalization

Normalization records:

- source format and EXIF orientation;
- source and target dimensions;
- operation mode;
- crop box;
- raw and clean hashes.

Unexpected substitution, undocumented crop, stale clean image, or dimension mismatch fails validation.

Coverage includes portrait, landscape, JPEG, PNG, WebP, EXIF rotation, and aspect-ratio boundaries.

### 15.2 Typography preflight

Before lettering, every authored code point is checked against configured fonts. Missing coverage blocks lettering and reports:

- Unicode code point;
- text item ID;
- fonts checked;
- supported remediation.

A project cannot reach `COMPLETE` with `.notdef` output. Tests cover Latin, Greek, Cyrillic, Arabic policy, CJK, emoji, combining marks, and bold spans. Only scripts with verified shaping/rendering support are advertised as supported.

## 16. Page and PDF QA

### 16.1 Page QA

Every composed page has a current record for:

- clipped text;
- text overlap;
- face/action obstruction;
- bubble-tail direction;
- reading order;
- accidental text or watermark;
- layout and border integrity.

Missing or stale page QA blocks finalization.

### 16.2 PDF verification

The exported PDF is decoded page by page and compared to source PNGs across full page content with a documented lossy tolerance. Four-corner sampling is insufficient.

Negative tests cover:

- erased center content;
- missing lettering;
- swapped pages;
- duplicate pages;
- corrupt PDF;
- page count and dimension mismatch.

## 17. Layouts and sample matrix

Add at least one four-panel layout. Golden composition/export tests exercise every supported layout.

Curated samples cover:

- two or more recurring characters;
- identity, wardrobe, prop, palette, and scene continuity;
- all layouts;
- dense dialogue;
- caption and SFX;
- portrait and landscape normalization;
- one transient repeat;
- one visual retry;
- one accepted warning;
- one hard failure;
- non-Latin font fallback;
- interrupted and resumed run.

Samples state clearly whether they prove deterministic mechanics or live visual quality.

## 18. Client auto-configuration

Initial supported stable clients:

- Codex;
- Hermes;
- Claude Desktop;
- Claude Code;
- Cursor;
- VS Code;
- Windsurf.

A client adapter defines detection, config location, parser, backup, idempotent mutation, verification, and rollback.

Setup sequence:

1. detect installed clients and config locations;
2. parse native config format;
3. refuse malformed config without overwriting it;
4. create timestamped backup;
5. install/update Skill and MCP command;
6. write atomically;
7. run client-independent MCP protocol smoke test;
8. rollback integration if verification fails;
9. report configured, skipped, unsupported, and failed clients separately.

Unknown clients are skipped. Repeat setup never duplicates entries.

## 19. Output roots

Defaults:

```text
Windows:   %USERPROFILE%\Documents\Comic Sol
macOS:     ~/Documents/Comic Sol
Linux:     ~/Comic Sol
Container: /data
```

WSL follows Linux unless the user explicitly selects a mounted Windows path.

Override:

```text
comic-sol setup --output-root PATH
```

Every project remains isolated beneath the configured root.

## 20. Bundled runtime and packaging

PyInstaller is the initial bundled-runtime tool. It packages:

- pinned Python runtime;
- Comic Sol engine and CLI;
- Pillow and MCP SDK;
- Skill, references, templates, and fonts;
- bundled provider adapters;
- license notices.

The design permits changing bundling tools if platform spikes prove PyInstaller unsuitable. The external CLI, project format, and installer behavior remain stable.

### 20.1 Distribution artifacts

| Platform | Artifacts |
|---|---|
| Windows | EXE installer, MSI enterprise installer |
| macOS | DMG, PKG |
| Debian/Ubuntu | DEB |
| Fedora/RHEL | RPM |
| Linux universal | AppImage |
| Container | OCI image and Compose example |
| Fallback | portable archive |

Each release includes:

- SHA-256 checksums;
- SBOM;
- version metadata;
- bundled license notices;
- signatures when signing credentials are available;
- upgrade and uninstall behavior.

Unsigned builds are labeled unsigned; they are never presented as signed.

## 21. Installer behavior

Installer sequence:

1. install executable and immutable assets;
2. choose or derive output root;
3. detect supported clients;
4. back up valid existing config;
5. install Skill and register `comic-sol mcp`;
6. run `comic-sol doctor`;
7. run protocol/tool-discovery smoke test;
8. rollback client changes if verification fails;
9. emit a factual installation report.

Uninstall removes binaries and integration entries. User projects remain unless the user explicitly selects deletion with a separate confirmation.

Upgrade preserves projects, configuration, client backups, and the previous installer version required for rollback.

## 22. Observability

Sanitized events cover:

- project creation;
- transition and blocking;
- generation attempt and retry category;
- promotion;
- validation result;
- lettering;
- composition;
- report render;
- export and PDF verification;
- invalidation and resume;
- override;
- transaction recovery;
- command failure category.

Events contain stable stage/action/category fields. They exclude secrets, prompt bodies, provider raw payloads, and absolute private paths.

A failed run must be diagnosable to the last successful stage and stable failure category using logs alone.

## 23. CI and release gates

### 23.1 Pull-request matrix

- Ubuntu;
- macOS Intel/ARM where runners permit;
- Windows native;
- WSL smoke environment;
- container.

Jobs separate:

- base deterministic installation without MCP/provider extras;
- MCP extra installation and protocol tests;
- provider contract tests using fakes;
- cross-process concurrency tests;
- crash/fault-injection tests;
- traversal, symlink, junction, and reparse tests;
- deterministic output tests;
- package smoke tests.

Actions are pinned to immutable commit SHAs. Dependency locks include hashes. Security audit results are visible and policy-driven.

### 23.2 Release gates

For every artifact on clean environments:

1. verify checksum, SBOM, metadata, and signature state;
2. install;
3. run doctor;
4. auto-configure client fixtures;
5. discover MCP tools;
6. initialize a project;
7. recover an interrupted project;
8. finalize a validated sample PDF;
9. upgrade from previous supported release;
10. uninstall;
11. prove project data remains.

A successful build alone is not a successful installer.

## 24. Required initial defect closures

Integrity Core must explicitly close these audited defects before packaging work claims stability:

1. final validation can pass with missing final artifacts;
2. export and terminal transitions bypass quality gates;
3. retry counters race across concurrent calls;
4. composition accepts manifest-controlled external paths;
5. multi-page composition can partially replace prior output;
6. project mutations can leave contradictory files after failure;
7. promotion archive selection races;
8. `BLOCKED` cannot resume;
9. source limits are not enforced at direct CLI/MCP boundaries;
10. MCP cannot render report or complete the documented lifecycle;
11. optional MCP dependency breaks the documented base suite;
12. documentation contains machine-specific paths;
13. CI does not continuously verify advertised platforms.

## 25. Milestone acceptance

### 25.1 Integrity Core complete

- All 13 required initial defects have regression tests and fixes.
- Existing supported project fixtures remain valid or migrate explicitly.
- Full base and MCP suites pass from clean locked environments.
- No new package/installer work bypasses engine gates.

### 25.2 Portable Product complete

- Stable CLI and MCP lifecycle parity.
- Hybrid provider contract with fake-provider tests.
- Supported client adapters configure, verify, and rollback fixtures.
- Cross-platform source-level CI is green.

### 25.3 Native Distribution complete

- Every required artifact installs and uninstalls in clean test environments.
- Bundled runtime needs no system Python.
- Upgrade/rollback and data preservation pass.
- Checksums, SBOM, licenses, and signature state ship.

### 25.4 Comic Quality complete

- QA evidence is hash-bound and check-specific.
- Normalization provenance and typography preflight are enforced.
- Page QA and full-content PDF verification gate completion.
- Four-panel layout and sample matrix pass.

## 26. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Native installer matrix dominates development | Reliability and portable product gates finish first; platform packaging remains isolated. |
| PyInstaller behaves differently across OSes | Validate with early disposable platform spikes; preserve external contracts if bundler changes. |
| Client config formats change | Version adapters, fail closed, backup, verify, and skip unknown formats. |
| Cross-platform lock semantics differ | Contract tests use real concurrent processes on every OS gate. |
| Visual QA remains subjective | Require hash-bound structured evidence and negative fixtures; keep similarity advisory. |
| Broad script support produces broken text | Advertise only verified shaping/font coverage; block missing glyphs. |
| Schema strengthening breaks old projects | Explicit migration with backup and fixture tests. |
| Installer auto-config surprises users | Report planned targets, backup first, idempotent writes, rollback on failure. |

## 27. Decision record

Approved decisions:

- Product target: open-source Skill/MCP installable by anyone.
- Platforms: Linux, macOS, Windows native, WSL, and container.
- Distribution target: all stable native formats listed in this spec.
- Runtime: bundle Python by default.
- Client setup: auto-detect and configure stable popular clients.
- Generation: agent-driven default with optional provider adapters.
- Interface: CLI + Skill/MCP; no GUI.
- Strategy: reliability-first incremental evolution; no rewrite.

## 28. Implementation planning boundary

This document defines product behavior and acceptance gates. The implementation plan must decompose work milestone by milestone, use TDD for every behavior change, preserve public submission isolation, and avoid starting installer implementation before Integrity Core gates pass.

No release is called “perfect.” Release readiness means every objective gate in this specification has current passing evidence.

## 29. Approval

The user approved architecture, reliability core, packaging/MCP/provider design, native distribution, testing, and comic-quality design in sequence on 2026-07-23. The user gave final approval on 2026-07-23. Implementation planning may proceed milestone by milestone.
