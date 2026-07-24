# Decision Log

Record durable implementation or execution decisions with:

- Decision and timestamp
- Confirmed evidence
- Alternatives considered
- Reason selected
- Security and rollback effects
- Source URL when external evidence is used
- Local validation result

Initial decision: `.agent/` is the cross-run state authority. A scheduler worktree is an execution environment, not the sole persistence mechanism.
