# EvidenceLoop v0.1.0

EvidenceLoop v0.1.0 is the initial public release of a fail-closed evidence and conformance protocol for coding agents.

## Included

- A deterministic fail-closed task-state machine.
- `VERIFYING -> DONE` as the only successful terminal transition.
- Acceptance-gated `DONE` with mandatory machine-readable results.
- Command evidence, external-source validation, freshness records, and research provenance.
- Failure fingerprinting, repair, strategy retirement, replanning, and bounded `BLOCKED` behavior.
- Process-aware project locks, interruption recovery, resumable `next_action`, and completed-run archives.
- A Python 3.11+ runtime with no third-party runtime dependencies.
- A Codex-compatible Skill distributed under the compatibility identifier `autonomous-completion-loop`.
- Project installation, conservative uninstall, templates, schemas, policies, examples, and security documentation.

## Verification

Release-candidate verification completed on Python 3.11.9:

- `python3 -m compileall acl_loop scripts tests` — exit code 0.
- `python3 scripts/run_test_suite.py` — 25/25 tests passed, exit code 0.
- A source wheel built and installed with `python3 -m pip install --no-deps --target ... .` — exit code 0.
- The installed package's CLI help, global Skill installation, and disposable-project installation all ran successfully.

## Current limitations

- The package is not published to PyPI; v0.1.0 installs from a source checkout or Git URL.
- A GitHub Actions Python-version matrix is not included in v0.1.0.
- Evidence Bundle manifest v0.1 and formal conformance levels remain roadmap work.
- Scheduled Task creation still requires the supported Codex or ChatGPT interface; EvidenceLoop does not create a substitute system scheduler.
- The `autonomous-completion-loop` Skill identifier and `acl-loop` command remain for compatibility and may require a documented migration in a future release.
- Version 0.1.0 is alpha software; public schemas may evolve with documented changelog and migration notes.
