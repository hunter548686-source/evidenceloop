# EvidenceLoop

**A fail-closed evidence and conformance protocol for coding agents.**

EvidenceLoop is an agent-independent verification layer for software work performed by Codex, Claude Code, Cursor, Ralph-style loops, CI jobs, or custom automation.

Agents may claim a task is complete. EvidenceLoop requires machine-checkable proof before a project can enter `DONE`.

## Why it exists

Coding agents are increasingly able to edit real repositories, but completion is often decided by model output or harness-specific logic. EvidenceLoop standardizes:

- legal task-state transitions;
- acceptance criteria and command evidence;
- failure classification, repair, and replanning;
- source provenance for externally researched facts;
- resumable `next_action` checkpoints;
- project locks and stale-lock recovery;
- fail-closed `DONE` and `BLOCKED` behavior.

EvidenceLoop does not replace an agent, orchestrator, issue tracker, or CI system. It sits beneath them as a portable completion-proof layer.

## Core rule

```text
An agent can report completion.
Only verified acceptance evidence can authorize DONE.
```

`DONE` is legal only through:

```text
VERIFYING -> DONE
```

and only when every mandatory acceptance item passes.

## Current capabilities

- Python standard-library runtime with no third-party runtime dependencies.
- Deterministic task-state validation and transition enforcement.
- Acceptance-gated completion.
- Failure counters, strategy retirement, replanning, and real blocking rules.
- URL-required research records and source-freshness checks.
- Process-aware expiring project locks.
- Idempotent project installation and conservative uninstall.
- Secret-safe project inspection.
- Resumable execution through project-local `.agent/` state.
- Codex Skill integration and optional Scheduled Task setup guidance.
- Automated conformance-oriented test suite.

## Quick start

```bash
python3 scripts/run_test_suite.py
python3 -m pip install .
python3 scripts/install_global_skill.py
python3 scripts/install_project_loop.py --project /absolute/path/to/git/project
```

Or invoke the CLI directly:

```bash
python3 -m acl_loop.cli validate-state --project /absolute/path/to/git/project
python3 -m acl_loop.cli inspect --project /absolute/path/to/git/project
python3 -m acl_loop.cli report --project /absolute/path/to/git/project
```

The primary installed command is `evidenceloop`. The legacy `acl-loop` command remains available in v0.1.0 for compatibility.

## State model

```text
INIT
INSPECTING
RESEARCH_NEEDED
RESEARCHING
FACT_CHECKING
PLANNING
EXECUTING
VERIFYING
REPAIRING
REPLANNING
DONE
BLOCKED
```

Important invariants:

- `DONE` cannot be entered from planning or execution states.
- Missing mandatory evidence fails closed.
- A third identical failure retires the current strategy and requires replanning.
- Multiple materially different failed strategies are required before a genuine `BLOCKED` result.
- `DONE` prevents further mutation.
- `BLOCKED` prevents meaningless retry and report churn until the named unblock condition changes.

## Repository layout

```text
acl_loop/       Core runtime
scripts/        Installation, validation, and test entrypoints
schemas/        Versioned state schemas
templates/      Project installation templates
.agents/skills/ Repository-discoverable Codex Skill mirror
skill/          Canonical Codex Skill source used by installers
acl_loop/resources/
                Packaged templates, schemas, policies, and Skill assets
examples/       Example workflows
docs/           Architecture, security, recovery, and operations
tests/          Automated tests and fixtures
```

## Verification

Run:

```bash
python3 scripts/run_test_suite.py
git diff --check
git status --short
```

The test suite covers installation, state transitions, acceptance gates, retries, source validation, locking, interruption recovery, terminal-state behavior, uninstall safety, and secret-safe inspection.

The CI matrix is configured for Python 3.11, 3.12, and 3.13. Each non-cancelled job is configured to record a JSON and text outcome summary, and to upload the full test evidence whenever the suite starts. A green CI run proves only that these commands passed in the listed jobs. It does not prove output quality, production readiness, security certification, adoption, or external users.

## Project status

Version 0.1.0 is the initial public release. EvidenceLoop is early-stage and maintainer-led. No public adoption, package-registry downloads, external-user count, or ecosystem usage is claimed.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Installation](docs/INSTALLATION.md)
- [Codex integration walkthrough](docs/CODEX_INTEGRATION.md)
- [Usage](docs/USAGE.md)
- [State machine](docs/STATE_MACHINE.md)
- [Research protocol](docs/RESEARCH_PROTOCOL.md)
- [Security](docs/SECURITY.md)
- [Recovery](docs/RECOVERY.md)
- [Uninstall](docs/UNINSTALL.md)
- [Roadmap](ROADMAP.md)
- [v0.1.0 release notes](docs/RELEASE_NOTES_v0.1.0.md)
- [Contributing](CONTRIBUTING.md)
- [Governance](GOVERNANCE.md)

## License

Apache License 2.0. See [LICENSE](LICENSE).
