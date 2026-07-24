# Contributing to EvidenceLoop

EvidenceLoop accepts focused contributions that improve verification, reproducibility, safety, interoperability, documentation, and tests.

## Before opening a change

1. Search existing issues and discussions.
2. Keep the scope narrow and independently verifiable.
3. Do not add network calls, telemetry, third-party runtime dependencies, or secret access without prior maintainer approval.
4. Do not weaken fail-closed behavior or acceptance requirements.

## Development setup

EvidenceLoop currently uses the Python standard library only.

```bash
python3 scripts/run_test_suite.py
```

## Required checks

Before submitting a pull request, run:

```bash
python3 scripts/run_test_suite.py
git diff --check
git status --short
```

Include the exact commands, exit codes, and relevant output in the pull-request description.

## Design rules

- An agent's statement is not acceptance evidence.
- Missing or stale mandatory evidence fails closed.
- `DONE` is legal only through `VERIFYING`.
- Existing project files and user instructions must be preserved.
- General project inspection must not read secret contents.
- Behavioral changes require focused tests.
- Documentation must distinguish confirmed behavior from planned behavior.

## Pull requests

A useful pull request contains:

- a clear problem statement;
- the smallest practical change;
- tests demonstrating the behavior;
- compatibility and migration notes when applicable;
- rollback instructions;
- no unrelated cleanup.

Maintainers may request changes or reject proposals that broaden scope without a measurable verification benefit.
