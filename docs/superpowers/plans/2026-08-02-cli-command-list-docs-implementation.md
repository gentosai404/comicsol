# CLI Command List Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep the README's CLI command summary synchronized with all ten commands exposed by the packaged entry point.

**Architecture:** Add one focused documentation contract test that isolates the README command-summary sentence and checks each public command as inline code. Make the smallest documentation correction needed to satisfy that contract; runtime code and CLI parsing remain unchanged.

**Tech Stack:** Python 3.11, standard-library `unittest`, Markdown.

## Global Constraints

- Update the README command summary to include `setup`, `repair`, and `uninstall`.
- Add a focused documentation regression test that requires the README summary to name every public CLI command currently exposed by the packaged entry point.
- Do not change command behavior, parser structure, installation instructions, or the documented 17-tool MCP contract.

---

### Task 1: Synchronize the README CLI command summary

**Files:**
- Modify: `tests/test_release_docs.py:14-20`
- Modify: `README.md:69-71`

**Interfaces:**
- Consumes: `ReleaseDocumentationTests.readme`, the existing UTF-8 README fixture loaded by `setUpClass`.
- Produces: A documentation contract asserting that the isolated CLI summary contains the ten public command names; no runtime interface changes.

- [ ] **Step 1: Write the failing documentation contract test**

Add this test after `test_readme_links_native_install_and_release_security`:

```python
    def test_readme_lists_every_public_cli_command(self):
        command_summary = self.readme.split("The CLI currently exposes ", 1)[1].split(
            " Machine-readable responses", 1
        )[0]
        for command in (
            "doctor", "init", "status", "validate", "resume", "finalize",
            "mcp", "setup", "repair", "uninstall",
        ):
            with self.subTest(command=command):
                self.assertIn(f"`{command}`", command_summary)
```

- [ ] **Step 2: Run the new test and verify RED**

Run:

```bash
python3.11 -m unittest tests.test_release_docs.ReleaseDocumentationTests.test_readme_lists_every_public_cli_command -v
```

Expected: FAIL subtests for `setup`, `repair`, and `uninstall`, proving the test detects the incomplete summary.

- [ ] **Step 3: Make the minimal README correction**

Replace the current command-summary paragraph with:

```markdown
The CLI currently exposes `doctor`, `init`, `status`, `validate`, `resume`,
`finalize`, `setup`, `repair`, and `uninstall`, plus the optional `mcp` launcher.
Machine-readable responses use one stable envelope containing `ok`, `command`,
`data`, and `error`.
```

- [ ] **Step 4: Run focused and full verification**

Run:

```bash
python3.11 -m unittest tests.test_release_docs -v
python3.11 -m unittest discover -s tests -v
git diff --check
```

Expected: both test commands report `OK`, and `git diff --check` produces no output.

- [ ] **Step 5: Review and commit the implementation**

Inspect `git status -sb` and `git diff`, confirm only the intended README and test changes are present, then run:

```bash
git add README.md tests/test_release_docs.py
git commit -m "docs: list all CLI commands in README"
```
