# Codex for Open Source — EvidenceLoop Application Draft

Official application: https://openai.com/form/codex-for-oss/

Verified on 2026-07-24. Do not submit until every `OWNER_INPUT_REQUIRED` field is supplied by the project owner.

## Verified public facts

- GitHub username: `hunter548686-source`
- Public repository: https://github.com/hunter548686-source/evidenceloop
- v0.1.0 release: https://github.com/hunter548686-source/evidenceloop/releases/tag/v0.1.0
- License: Apache-2.0
- Current automated test suite: 25 tests; 25/25 passed for the v0.1.0 release candidate
- Current maintenance state: public v0.1.0 initial release, maintainer-led governance, public roadmap, and active issue triage
- Current open Issue count: 5
- Issue provenance: all five are maintainer-created roadmap tasks, not external-user feedback
- PyPI status: not published
- Adoption status: no stars, downloads, external users, or ecosystem adoption are claimed in this application

## Owner-supplied fields

- First name: `OWNER_INPUT_REQUIRED`
- Last name: `OWNER_INPUT_REQUIRED`
- Email associated with the applicant's ChatGPT account: `OWNER_INPUT_REQUIRED`
- OpenAI Organization ID: `OWNER_INPUT_REQUIRED`

## GitHub fields

- GitHub username: `hunter548686-source`
- GitHub repository URL: `https://github.com/hunter548686-source/evidenceloop`

## Role

Select: **Primary maintainer**

Evidence-backed draft:

> I am the project owner and primary maintainer. I am responsible for EvidenceLoop's state model, evidence protocol, safety boundaries, release management, issue triage, documentation, compatibility, and security maintenance.

## Why does this repository qualify?

411 characters; form limit: 500.

> EvidenceLoop is an agent-independent, fail-closed evidence and conformance protocol for coding agents. It makes DONE acceptance-gated and records command evidence, source provenance, failure escalation, locking, and recovery across Codex and other agent workflows. Public v0.1.0 includes a standard-library Python runtime, a Codex-compatible Skill, 25 passing tests, and an active five-issue maintainer roadmap.

## Requested support

- API credits for the project: **Yes**
- Codex Security: **Not selected in the current recommendation; owner may reconsider if the project's security-review scope materially expands**

## OpenAI Organization ID

`OWNER_INPUT_REQUIRED`

## How will you use API credits for your project?

435 characters; form limit: 500.

> We will use API credits to maintain Codex integrations; reproduce reported failures in disposable repositories; evaluate agents against adversarial completion cases; review contributions; and build public regression and conformance fixtures. Results will be documented in issues, tests, and releases to improve evidence quality, failure recovery, safety boundaries, and interoperability for open-source maintainers using coding agents.

## Anything else we should know?

441 characters; form limit: 500.

> EvidenceLoop is not another coding agent or orchestrator. It is a portable proof layer that can complement Codex, CI systems, and other agent harnesses. The v0.1.0 runtime has no third-party runtime dependencies and tests fail-closed completion, secret-safe inspection, interruption recovery, source validation, locking, and illegal transitions. This is a new project; we are not claiming stars, downloads, external users, or broad adoption.

## Submission gate

Do not submit until all are true:

- every `OWNER_INPUT_REQUIRED` field is supplied and checked by the owner;
- the owner confirms the ChatGPT-account email and OpenAI Organization ID;
- the GitHub profile remains public;
- the repository and release remain public;
- no unsupported adoption metric is added;
- the owner reviews the current recommendation in `OPENAI_APPLICATION_READY.md`.
