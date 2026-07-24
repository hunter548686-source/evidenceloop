## What changed

Describe the smallest complete change and the problem it solves.

## Verification

List the exact commands, exit codes, and relevant redacted results.

## Compatibility and rollback

Describe schema, CLI, state, installation, or migration effects and how to revert the change safely.

## Checklist

- [ ] The change is focused and contains no unrelated cleanup.
- [ ] Fail-closed behavior and acceptance gates are preserved.
- [ ] Tests cover behavioral changes.
- [ ] Public documentation is updated when behavior or compatibility changes.
- [ ] No credentials, `.env` contents, private keys, private paths, customer data, or unsupported claims are included.
- [ ] `python3 scripts/run_test_suite.py` passes.
- [ ] `git diff --check` passes.
