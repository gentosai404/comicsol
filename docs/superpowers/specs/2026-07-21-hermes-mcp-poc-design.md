# Comic Sol Hermes MCP Proof-of-Concept Design

**Topic:** Native Hermes MCP adapter
**Date:** 2026-07-21

## 1. Goal

Expose Comic Sol's existing deterministic Python pipeline as native Hermes tools without replacing the Codex Skill or duplicating pipeline logic.

The Codex Skill remains responsible for creative reasoning, planning, image generation, and visual QA. The MCP server is a local `stdio` adapter for deterministic lifecycle, validation, cache, lettering, composition, and PDF operations.

## 2. Architecture

```text
Hermes Agent
  ↕ MCP stdio
scripts/mcp_server.py
  ↕ direct Python calls
existing Comic Sol modules
  ↕
/home/acer/comic-sol-output/<project-id>
```

- Transport: local `stdio` only.
- SDK: official Python MCP SDK, exactly `mcp==1.28.1`.
- Runtime: isolated Python 3.11 virtual environment with existing `Pillow==11.3.0` requirement.
- Adapter: direct imports from existing `scripts/` modules; no subprocess output parsing.
- Core pipeline files remain unchanged unless a verified adapter defect requires a minimal fix.

## 3. Tool Surface

The server exposes 14 tools:

| Tool | Core boundary | Result |
|---|---|---|
| `comic_doctor` | `doctor` | Health and check messages |
| `comic_init` | `init_project` | New project ID |
| `comic_status` | `read_json(project.json)` | Manifest object |
| `comic_transition` | `transition` | Updated manifest |
| `comic_validate` | `validate_project` | Validation issue array |
| `comic_resume_plan` | `build_resume_plan` | Resume action array |
| `comic_invalidate` | `invalidate_from` | Removed artifact names |
| `comic_record_stage` | `record_stage` | Recorded stage summary |
| `comic_record_attempt` | `record_generation_attempt` | Retry counters |
| `comic_promote_attempt` | `promote_attempt` | Accepted relative path |
| `comic_override_panel` | `record_override` | Acceptance confirmation |
| `comic_letter` | `letter_project` | Lettered relative paths |
| `comic_compose` | `compose_project` | Composed relative paths |
| `comic_export` | `export_pdf` | PDF relative path |

`comic_init` accepts UTF-8 source text and a JSON request object. It never accepts an input filesystem path. Attempt tools accept project-relative paths, then existing Comic Sol containment checks enforce project boundaries.

## 4. Filesystem Security

The configured root is `/home/acer/comic-sol-output`.

- Server startup requires an absolute root path.
- Project IDs must match Comic Sol's canonical identifier pattern.
- Project resolution uses `Path.resolve()` and `Path.is_relative_to()` against the resolved root.
- Absolute project paths, separators, traversal segments, sibling-prefix tricks, and symlink escapes are rejected.
- Existing core containment validation remains active for attempt paths.
- Server exposes no arbitrary shell command or generic filesystem tool.
- Error messages report operation failures but never include environment variables or credentials.

## 5. Errors and Results

- Successful tool calls return JSON-serializable values with project-relative artifact paths.
- Validation findings are normal results, not protocol failures.
- Invalid input, unsafe paths, missing artifacts, illegal lifecycle transitions, and rendering/export failures become MCP `ToolError` results.
- Tool errors must not terminate the long-lived `stdio` server.
- `comic_doctor` returns `healthy` plus individual messages so callers can distinguish a failing runtime from transport failure.

## 6. Repository Changes

```text
requirements-mcp.txt
scripts/mcp_server.py
tests/test_mcp_server.py
README.md
docs/superpowers/specs/2026-07-21-hermes-mcp-poc-design.md
docs/superpowers/plans/2026-07-21-hermes-mcp-poc-plan.md
```

`requirements.txt` remains the deterministic core dependency file. `requirements-mcp.txt` adds only the optional exact MCP SDK pin.

## 7. Hermes Registration

Hermes config entry:

```yaml
mcp_servers:
  comic-sol:
    command: /home/acer/.venvs/comic-sol-mcp/bin/python
    args:
      - /mnt/c/Users/acer/Projects/comic-sol/scripts/mcp_server.py
      - --root
      - /home/acer/comic-sol-output
    timeout: 120
    connect_timeout: 60
    sampling:
      enabled: false
```

Sampling is disabled because this server exposes deterministic operations only. Hermes restart is required for native tool discovery.

## 8. Verification

- Unit tests cover absolute-root enforcement, traversal rejection, sibling-prefix rejection, and symlink escape rejection.
- MCP protocol smoke test starts the real server over `stdio`, discovers exactly 14 tools, and exercises every tool against disposable copies of project data. Mutating tools never touch the checked-in sample.
- Expected domain rejection for a non-overridable accepted panel counts as a successful safety test for `comic_override_panel`.
- Existing complete suite runs under Python 3.11 with Pillow 11.3.0.
- Final checks include `pip check`, server help/startup, Hermes config inspection, and repository diff review.

## 9. Non-Goals

- No one-call creative `create_comic` orchestration.
- No LLM sampling or image-generation calls inside MCP.
- No HTTP transport, remote access, authentication layer, or multi-user service.
- No arbitrary project root supplied per tool call.
- No rewrite of Comic Sol core or Codex Skill.
