# Governance

EvidenceLoop is currently maintained under a lightweight maintainer-led model suitable for an early-stage open-source project.

## Roles

### Maintainer

Maintainers may:

- review and merge changes;
- triage issues and security reports;
- publish releases;
- evolve schemas and compatibility policy;
- appoint additional maintainers based on sustained contributions.

### Contributor

Any participant who submits code, documentation, tests, design feedback, bug reports, or interoperability results is a contributor.

## Decision process

Routine, reversible changes may be accepted through normal pull-request review.

The following require an explicit public design decision before implementation:

- incompatible schema changes;
- relaxation of fail-closed rules;
- new network access or telemetry;
- new third-party runtime dependencies;
- changes to secret-handling boundaries;
- changes to license or governance;
- removal of previously supported state or evidence formats.

## Compatibility

EvidenceLoop will version public schemas and document migrations. Until a stable 1.0 release, incompatible changes may occur, but they must be disclosed in the changelog and release notes.

## Maintainer succession

Additional maintainers may be appointed after demonstrating sustained, technically sound, security-conscious participation. Inactive maintainers may be moved to emeritus status after a public notice period.

## Enforcement

Participation is governed by `CODE_OF_CONDUCT.md`. Security-sensitive reports should follow `SECURITY.md` rather than being disclosed in a public issue.
