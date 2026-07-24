# Codex for Open Source — Application Draft

Official program page: https://openai.com/form/codex-for-oss/

Do not submit until the repository is public and the factual fields below have been verified.

## Required owner-supplied fields

- First name
- Last name
- Email associated with the applicant's ChatGPT account
- Public GitHub username
- Public EvidenceLoop repository URL
- OpenAI Organization ID

## Role

**Primary maintainer**

Draft response:

> I am the primary maintainer and project owner. I designed the state machine, evidence model, safety boundaries, recovery protocol, installation workflow, and test suite, and I am responsible for issue triage, releases, documentation, compatibility, and security maintenance.

## Why the repository qualifies

Maximum allowed by the form: 500 characters.

Draft:

> EvidenceLoop provides an agent-independent, fail-closed verification layer for coding agents. It standardizes legal completion states, acceptance evidence, source provenance, failure escalation, recovery, locking, and reproducible completion records across Codex and other agent workflows. It addresses a growing ecosystem need: independently proving that agent-produced software work is actually complete.

Do not add stars, downloads, installations, users, issues, pull requests, or release claims unless they are real and visible at submission time.

## Requested support

- API credits for the project
- Codex Security only if the repository and program review show that it is applicable

## API-credit use

Maximum allowed by the form: 500 characters.

Draft:

> We will use API credits to maintain Codex adapters, reproduce community issues, evaluate agent behavior against adversarial completion cases, review contributions, generate regression fixtures, and run public conformance tests across real open-source repositories. The results will improve evidence quality, safety boundaries, release checks, and interoperability for maintainers using coding agents.

## Anything else

Maximum allowed by the form: 500 characters.

Draft:

> EvidenceLoop is intentionally not another coding agent or orchestrator. It is a portable proof layer that can complement Codex, CI systems, and other agent harnesses. The initial implementation uses only the Python standard library and includes automated tests for fail-closed completion, secret-safe inspection, interruption recovery, source validation, locking, and invalid state transitions.

## Submission gate

Submit only when all are true:

- repository is public;
- repository URL is confirmed;
- GitHub profile is public;
- first release or visible maintenance activity exists;
- README and license render correctly;
- all tests pass from the public repository checkout;
- no private paths, credentials, customer data, or unsupported adoption claims remain;
- OpenAI Organization ID is supplied by the owner.
