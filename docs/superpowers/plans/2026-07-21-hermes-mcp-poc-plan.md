# Comic Sol Hermes MCP Proof-of-Concept Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers/subagent-driven-development (recommended) or superpowers/executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify a native Hermes MCP `stdio` adapter over Comic Sol's existing deterministic pipeline.

**Architecture:** `scripts/mcp_server.py` uses official FastMCP and direct imports from existing core modules. A single absolute output root and canonical project IDs constrain every operation; MCP adds protocol adaptation only.

**Tech Stack:** Python 3.11, Pillow 11.3.0, MCP Python SDK 1.28.1, `unittest`, Hermes native MCP client.

## Global Constraints

- Keep Codex Skill as creative workflow owner; MCP remains deterministic adapter.
- Pin `mcp==1.28.1` exactly in optional `requirements-mcp.txt`.
- Use local `stdio`; no HTTP server or sampling.
- Root all project operations at `/home/acer/comic-sol-output`.
- Reject traversal, absolute project paths, sibling-prefix tricks, and symlink escapes.
- Preserve existing Comic Sol core behavior and project format.
- Return structured JSON-compatible results and MCP tool errors.
- Exercise all 14 tools through a real MCP client session.

---

### Task 1: Secure Adapter and Dependency

**Files:**
- Create: `requirements-mcp.txt`
- Create: `scripts/mcp_server.py`
- Test: `tests/test_mcp_server.py`

**Interfaces:**
- Consumes: existing lifecycle, validation, lettering, composition, and export functions.
- Produces: `_configure_root(path: Path) -> Path`, `_resolve_project(project_id: str) -> Path`, `mcp: FastMCP`, and 14 `comic_*` tools.

- [ ] **Step 1: Write failing containment and tool-discovery tests**

Add `unittest` cases that import `mcp_server`, configure a temporary root, reject `../escape`, reject an absolute path, reject a child symlink targeting outside the root, and assert MCP exposes the 14 approved names.

- [ ] **Step 2: Run focused tests and verify failure**

Run:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest tests.test_mcp_server -v
```

Expected: failure from absent or incomplete secure adapter behavior.

- [ ] **Step 3: Implement minimal secure FastMCP adapter**

Use `FastMCP(name="Comic Sol", instructions="Deterministic Comic Sol project tools")`, `Path.is_relative_to()`, Comic Sol's identifier pattern, direct core calls, `ToolError`, project-relative output paths, and `mcp.run(transport="stdio")`.

- [ ] **Step 4: Add optional exact dependency pin**

`requirements-mcp.txt`:

```text
mcp==1.28.1
```

- [ ] **Step 5: Run focused tests**

Run the focused unittest command. Expected: all focused tests pass.

- [ ] **Step 6: Commit adapter unit**

```bash
git add requirements-mcp.txt scripts/mcp_server.py tests/test_mcp_server.py
git commit -m "feat: add secure Comic Sol MCP adapter"
```

---

### Task 2: Real Protocol Smoke Test and Documentation

**Files:**
- Modify: `tests/test_mcp_server.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: executable server and 14 registered tool names from Task 1.
- Produces: real `stdio` protocol test covering discovery, normal results, mutations on disposable projects, and safe domain rejection.

- [ ] **Step 1: Write failing `stdio` integration test**

Use `mcp.client.stdio.stdio_client`, `ClientSession`, and `StdioServerParameters` to launch the actual server with a temporary root. Copy `samples/sunlight-courier` into that root, create a retained panel attempt inside the copy, then call all 14 tools. Assert successful results for deterministic operations and `isError` for an invalid override of an already accepted panel.

- [ ] **Step 2: Run integration test and verify failure**

Run:

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest tests.test_mcp_server.McpProtocolTests -v
```

Expected: failure until protocol schemas/results match the SDK.

- [ ] **Step 3: Apply smallest adapter fixes**

Fix only mismatched schemas, annotations, or result normalization revealed by the real protocol test. Do not change pipeline logic.

- [ ] **Step 4: Document isolated setup and Hermes config**

README commands must create `/home/acer/.venvs/comic-sol-mcp`, install both requirement files, create `/home/acer/comic-sol-output`, register `comic-sol` with `hermes mcp add`, and state that Hermes restart is required.

- [ ] **Step 5: Run focused protocol tests**

Run both MCP test classes. Expected: all pass and exactly 14 tools discovered.

- [ ] **Step 6: Commit protocol coverage and docs**

```bash
git add tests/test_mcp_server.py README.md
git commit -m "test: verify Comic Sol MCP protocol"
```

---

### Task 3: Install, Register, and Verify in Hermes

**Files:**
- Modify outside repo: `/home/acer/.venvs/comic-sol-mcp/`
- Modify outside repo: `/home/acer/.hermes/config.yaml`

**Interfaces:**
- Consumes: committed adapter path and requirements.
- Produces: installed isolated runtime and persistent Hermes MCP server config.

- [ ] **Step 1: Build isolated runtime**

```bash
python3.11 -m venv /home/acer/.venvs/comic-sol-mcp
/home/acer/.venvs/comic-sol-mcp/bin/pip install -r requirements.txt -r requirements-mcp.txt
/home/acer/.venvs/comic-sol-mcp/bin/pip check
```

Expected: `No broken requirements found.`

- [ ] **Step 2: Register server through Hermes CLI**

```bash
hermes mcp add comic-sol \
  --command /home/acer/.venvs/comic-sol-mcp/bin/python \
  --args /mnt/c/Users/acer/Projects/comic-sol/scripts/mcp_server.py --root /home/acer/comic-sol-output
```

Then set timeout and disabled sampling using supported Hermes config commands or a minimal YAML edit if CLI has no flags for them.

- [ ] **Step 3: Inspect registration**

```bash
hermes mcp list
```

Expected: `comic-sol` configured as a `stdio` server with exact command and arguments.

- [ ] **Step 4: Verify server handshake independently**

Run MCP protocol tests against the registered executable and exact root. Expected: initialization, tool discovery, and calls succeed.

---

### Task 4: Regression and Branch Completion

**Files:**
- Review: all changed repository files.

**Interfaces:**
- Consumes: completed adapter, tests, docs, runtime, and config.
- Produces: verified branch ready for review/merge.

- [ ] **Step 1: Run complete suite**

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python -m unittest discover -s tests -v
```

Expected: all tests pass; only platform-specific pre-existing skips allowed.

- [ ] **Step 2: Run final runtime checks**

```bash
/home/acer/.venvs/comic-sol-mcp/bin/python scripts/comic_sol.py doctor --output-root /home/acer/comic-sol-output
/home/acer/.venvs/comic-sol-mcp/bin/python scripts/mcp_server.py --help
/home/acer/.venvs/comic-sol-mcp/bin/pip check
```

Expected: doctor PASS, help exits 0, dependency check clean.

- [ ] **Step 3: Review diff and repository state**

```bash
git diff --check
git status --short --branch
git log --oneline -5
```

Expected: no whitespace errors, only intended changes, commits on `ai/comic-sol-mcp-poc`.

- [ ] **Step 4: Commit any final verified adjustment**

If final verification required a change:

```bash
git add <exact-changed-files>
git commit -m "fix: finalize Comic Sol MCP integration"
```

Otherwise create no empty commit.
