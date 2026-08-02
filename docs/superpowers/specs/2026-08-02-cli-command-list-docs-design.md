# CLI Command List Documentation Design

## Goal

Keep the README's public CLI command summary aligned with the commands exposed by
`comic-sol --help`. The current summary omits the existing `setup`, `repair`, and
`uninstall` commands.

## Scope

- Update the README command summary to include `setup`, `repair`, and `uninstall`.
- Add a focused documentation regression test that requires the README summary to
  name every public CLI command currently exposed by the packaged entry point.
- Do not change command behavior, parser structure, installation instructions, or
  the documented 17-tool MCP contract.

## Implementation

Extend `tests/test_release_docs.py` with one assertion-driven test over the existing
README fixture. The test will enumerate the ten public commands from the packaged
CLI and fail until the README command-summary sentence includes all of them. Then
update only that README sentence.

There is no new runtime data flow or error handling: this is a documentation-only
correction guarded by an offline unit test.

## Verification

Run the new documentation test first and observe it fail because the three
integration commands are absent from the summary. After updating the README, run:

```bash
python3.11 -m unittest tests.test_release_docs -v
python3.11 -m unittest discover -s tests -v
git diff --check
```

The PR is complete when the targeted and full deterministic suites pass, the diff
contains only this spec, the focused test, and the README correction, and the
working tree has no unintended changes.
