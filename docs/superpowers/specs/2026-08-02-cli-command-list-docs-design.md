# CLI Command List Documentation Design

## Goal

Keep the README's public CLI command summary aligned with the commands exposed by
`comic-sol --help`. The current summary omits the existing `setup`, `repair`, and
`uninstall` commands.

## Scope

- Update the README command summary to include `setup`, `repair`, and `uninstall`.
- Do not change command behavior, parser structure, installation instructions, or
  the documented 17-tool MCP contract.

## Implementation

Update only the README command-summary sentence, using the packaged CLI's `--help`
output as the source of truth. A source-text assertion would be a brittle change
detector rather than a behavioral test, so this human-facing prose correction does
not add a new test. There is no new runtime data flow or error handling.

## Verification

Before and after updating the README, inspect the packaged CLI's `--help` output.
Then run:

```bash
python3.11 -m comic_sol_product.cli --help
python3.11 -m unittest tests.test_release_docs -v
python3.11 -m unittest discover -s tests -v
git diff --check
```

The PR is complete when the targeted and full deterministic suites pass, the diff
contains only the planning documents and the README correction, and the working
tree has no unintended changes.
