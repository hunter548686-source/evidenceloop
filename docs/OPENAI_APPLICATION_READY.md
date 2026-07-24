# EvidenceLoop — Codex for Open Source Application Handoff

Official application: https://openai.com/form/codex-for-oss/

Prepared on 2026-07-24 from the live public repository and release. This document prepares the application; it does not claim the form was submitted.

## Copy-ready English answers

### GitHub username

`hunter548686-source`

Evidence: [public GitHub profile](https://github.com/hunter548686-source)

### GitHub repository URL

`https://github.com/hunter548686-source/evidenceloop`

Evidence: [public EvidenceLoop repository](https://github.com/hunter548686-source/evidenceloop)

### Maintainer role

Select: **Primary maintainer**

> I am the project owner and primary maintainer. I am responsible for EvidenceLoop's state model, evidence protocol, safety boundaries, release management, issue triage, documentation, compatibility, and security maintenance.

Evidence: [Governance](https://github.com/hunter548686-source/evidenceloop/blob/main/GOVERNANCE.md), [Contributing](https://github.com/hunter548686-source/evidenceloop/blob/main/CONTRIBUTING.md), [Security policy](https://github.com/hunter548686-source/evidenceloop/blob/main/SECURITY.md)

### Why does this repository qualify?

411 characters; form limit: 500.

> EvidenceLoop is an agent-independent, fail-closed evidence and conformance protocol for coding agents. It makes DONE acceptance-gated and records command evidence, source provenance, failure escalation, locking, and recovery across Codex and other agent workflows. Public v0.1.0 includes a standard-library Python runtime, a Codex-compatible Skill, 25 passing tests, and an active five-issue maintainer roadmap.

Evidence: [README](https://github.com/hunter548686-source/evidenceloop#readme), [v0.1.0 release](https://github.com/hunter548686-source/evidenceloop/releases/tag/v0.1.0), [state machine](https://github.com/hunter548686-source/evidenceloop/blob/main/docs/STATE_MACHINE.md), [release verification](https://github.com/hunter548686-source/evidenceloop/blob/main/docs/RELEASE_NOTES_v0.1.0.md), [25-test suite](https://github.com/hunter548686-source/evidenceloop/blob/main/tests/test_acl_loop.py), [five open roadmap Issues](https://github.com/hunter548686-source/evidenceloop/issues)

### Requested support

- API credits for the project: **Select**
- Codex Security: **Do not select in the current recommendation; reconsider only if the owner wants it and the security-review scope expands**

Evidence: [public roadmap](https://github.com/hunter548686-source/evidenceloop/blob/main/ROADMAP.md), [open maintainer Issues](https://github.com/hunter548686-source/evidenceloop/issues)

### How will you use API credits for your project?

435 characters; form limit: 500.

> We will use API credits to maintain Codex integrations; reproduce reported failures in disposable repositories; evaluate agents against adversarial completion cases; review contributions; and build public regression and conformance fixtures. Results will be documented in issues, tests, and releases to improve evidence quality, failure recovery, safety boundaries, and interoperability for open-source maintainers using coding agents.

Evidence: [roadmap](https://github.com/hunter548686-source/evidenceloop/blob/main/ROADMAP.md), [Codex integration Issue](https://github.com/hunter548686-source/evidenceloop/issues/1), [conformance levels Issue](https://github.com/hunter548686-source/evidenceloop/issues/3), [Evidence Bundle Issue](https://github.com/hunter548686-source/evidenceloop/issues/4)

### Anything else we should know?

441 characters; form limit: 500.

> EvidenceLoop is not another coding agent or orchestrator. It is a portable proof layer that can complement Codex, CI systems, and other agent harnesses. The v0.1.0 runtime has no third-party runtime dependencies and tests fail-closed completion, secret-safe inspection, interruption recovery, source validation, locking, and illegal transitions. This is a new project; we are not claiming stars, downloads, external users, or broad adoption.

Evidence: [architecture](https://github.com/hunter548686-source/evidenceloop/blob/main/docs/ARCHITECTURE.md), [package metadata](https://github.com/hunter548686-source/evidenceloop/blob/main/pyproject.toml), [security implementation notes](https://github.com/hunter548686-source/evidenceloop/blob/main/docs/SECURITY.md), [test suite](https://github.com/hunter548686-source/evidenceloop/blob/main/tests/test_acl_loop.py)

## Owner input still required

- First name: `OWNER_INPUT_REQUIRED`
- Last name: `OWNER_INPUT_REQUIRED`
- Email associated with the owner's ChatGPT account: `OWNER_INPUT_REQUIRED`
- OpenAI Organization ID: `OWNER_INPUT_REQUIRED`
- Final confirmation of requested checkboxes: `OWNER_INPUT_REQUIRED`
- Final owner review and form submission: `OWNER_INPUT_REQUIRED`

Do not infer these values from repository metadata or a GitHub account.

## Current application strengths

- A live public Apache-2.0 repository and an immutable v0.1.0 release exist.
- The product has a clear ecosystem role: an agent-independent proof layer rather than another agent wrapper.
- The implementation is executable, standard-library-only at runtime, and backed by 25 passing tests.
- Safety, governance, contribution, recovery, and compatibility rules are public.
- Five roadmap Issues make the immediate maintainer workload visible and falsifiable.
- The repository includes a Codex-compatible Skill and a concrete Codex integration roadmap item.

## Current application weaknesses

- This is the first public release, so there is not yet a public history of sustained maintenance.
- No stars, downloads, external users, external Issues, pull requests, or ecosystem adoption are claimed.
- The Python 3.11–3.13 GitHub Actions matrix is still an open roadmap item.
- There is no follow-up release or public resolution of a maintenance Issue yet.
- PyPI publication is intentionally out of scope for v0.1.0.

## Recommendation

**Prepare now, but do not submit today.** First close the CI-matrix Issue, publish the Codex integration walkthrough, and complete at least one visible follow-up maintenance cycle such as an Issue resolution or corrective release. Then refresh the factual counts and submit with the owner-only fields.

This recommendation follows the current official program criteria, which emphasize meaningful usage, ecosystem importance, and evidence of active maintenance. EvidenceLoop already has a clear importance argument, but its public maintenance history is only beginning.
