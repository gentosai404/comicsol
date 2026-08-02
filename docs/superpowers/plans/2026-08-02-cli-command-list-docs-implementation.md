# CLI Command List Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct the README's CLI command summary so it names all ten commands exposed by the packaged entry point.

**Architecture:** Treat the packaged CLI's `--help` output as the source of truth and make the smallest matching prose correction in the README. Human-facing prose does not receive a brittle source-text assertion; runtime code and CLI parsing remain unchanged.

**Tech Stack:** Python 3.11, standard-library `unittest`, Markdown.

## Global Constraints

- Update the README command summary to include `setup`, `repair`, and `uninstall`.
- Do not change command behavior, parser structure, installation instructions, or the documented 17-tool MCP contract.

---

### Task 1: Synchronize the README CLI command summary

**Files:**
- Modify: `README.md:69-71`

**Interfaces:**
- Consumes: The ten-command list emitted by `python3.11 -m comic_sol_product.cli --help`.
- Produces: A corrected human-facing README summary; no runtime interface changes.

- [ ] **Step 1: Confirm the packaged CLI command list**

Run:

```bash
python3.11 -m comic_sol_product.cli --help
```

Expected: the positional command list contains `doctor`, `init`, `status`,
`validate`, `resume`, `finalize`, `mcp`, `setup`, `repair`, and `uninstall`.

- [ ] **Step 2: Make the minimal README correction**

Replace the current command-summary paragraph with:

```markdown
The CLI currently exposes `doctor`, `init`, `status`, `validate`, `resume`,
`finalize`, `setup`, `repair`, and `uninstall`, plus the optional `mcp` launcher.
Machine-readable responses use one stable envelope containing `ok`, `command`,
`data`, and `error`.
```

- [ ] **Step 3: Run focused and full verification**

Run:

```bash
python3.11 -m comic_sol_product.cli --help
python3.11 -m unittest tests.test_release_docs -v
python3.11 -m unittest discover -s tests -v
git diff --check
```

Expected: `--help` still lists all ten commands, both test commands report `OK`,
and `git diff --check` produces no output.

- [ ] **Step 4: Review and commit the implementation**

Inspect `git status -sb` and `git diff`, confirm only the intended README change is present, then run:

```bash
git add README.md
git commit -m "docs: list all CLI commands in README"
```
