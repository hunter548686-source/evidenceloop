<!-- AUTONOMOUS_COMPLETION_LOOP:START -->
## EvidenceLoop

Invoke `$autonomous-completion-loop` for continuous execution, automatic correction, evidence-backed external research, or continuation from `.agent/TASK_STATE.json`.

```text
read state → inspect real state → acquire lock → select smallest verifiable action
→ research official sources when needed → execute → verify → save evidence
→ update next_action → release lock
```

Do not read secrets or perform commit, push, merge, release, deployment, paid, destructive, or irreversible actions. `DONE` is allowed only from `VERIFYING` after mandatory acceptance passes. `DONE` is read-only. `BLOCKED` checks only its named unblock condition.
<!-- AUTONOMOUS_COMPLETION_LOOP:END -->
