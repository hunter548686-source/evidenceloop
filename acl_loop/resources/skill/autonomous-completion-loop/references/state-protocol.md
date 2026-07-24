# State Protocol Reference

## Transition authority

The canonical transition table is implemented in `acl_loop/core.py`. Do not invent transitions in prompts.

The only terminal success transition is `VERIFYING → DONE`, after all mandatory acceptance results are true. `PLANNING → DONE`, `EXECUTING → DONE`, and `REPAIRING → DONE` are rejected.

## Persistence

`TASK_STATE.json` is updated atomically. `next_action` must describe the next smallest verifiable step, not a vague project objective. `PROGRESS.md` records human-readable transition evidence.

## Terminal behavior

- `DONE`: read-only; preserve evidence; disable continuation when possible.
- `BLOCKED`: check only the named external condition; do not retry unchanged work or repeat unchanged reports.

## Recovery

After interruption, validate JSON, inspect the real project, reconcile incomplete work, acquire the shared lock, and resume from `next_action`. Do not infer success from a stale status field.
