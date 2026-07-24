# EvidenceLoop Roadmap

EvidenceLoop is an early-stage protocol and reference implementation. Roadmap items describe planned maintainer work, not delivery dates or adoption claims.

## Near-term work

1. **GitHub Actions CI matrix for Python 3.11–3.13**
   - Run the complete conformance-oriented suite on supported Python versions.
   - Publish exact pass/fail evidence without treating CI success as product-quality proof.

2. **Evidence Bundle manifest v0.1**
   - Define a portable manifest for commands, inputs, outputs, exit codes, source records, acceptance results, and lineage.
   - Specify validation and forward-compatibility rules.

3. **Generic CLI adapter example**
   - Demonstrate how an agent or orchestrator can invoke EvidenceLoop without depending on a specific vendor harness.
   - Keep the example deterministic and free of third-party runtime dependencies.

4. **Codex integration walkthrough**
   - Document installation, Skill invocation, state continuation, failure repair, and evidence review in a disposable repository.
   - Separate verified behavior from optional Scheduled Task setup.

5. **Conformance test levels**
   - Define progressive levels for state validity, evidence completeness, recovery, failure escalation, and terminal behavior.
   - Publish machine-readable expectations before claiming cross-tool conformance.

## Contribution path

Each roadmap item should have a public issue before implementation. Proposed changes must include an acceptance method, compatibility impact, and rollback plan.
