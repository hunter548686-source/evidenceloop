# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x | Yes |
| Earlier versions | No |

## Reporting a vulnerability

Do not open a public issue for a vulnerability that could expose secrets, enable unsafe command execution, bypass evidence gates, corrupt project state, or weaken fail-closed behavior.

Use the repository's private vulnerability-reporting feature. Include:

- affected version or commit;
- reproduction steps;
- expected and actual behavior;
- security impact;
- suggested mitigation, when available.

Do not include real credentials, tokens, private keys, customer data, or unrelated private files in a report.

## Security boundaries

EvidenceLoop is designed to avoid reading secret contents during general project inspection and does not authorize Git push, deployment, paid operations, destructive database actions, or operating-system security reduction.

See [docs/SECURITY.md](docs/SECURITY.md) for the implementation boundaries and current safety verification.
