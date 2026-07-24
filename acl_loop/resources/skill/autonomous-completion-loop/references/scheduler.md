# Scheduler Reference

The canonical names, cadence, timezone, and prompts live in `config/schedule-policy.yaml`.

## Local execution facts

- Local project Scheduled Tasks require the machine to be powered on, the Codex desktop application running, and the folder available.
- Scheduled Task management is performed in the official desktop/web UI, not through a Codex CLI or IDE management interface.
- A web task cannot access a local project folder.
- A scheduler-created worktree is isolated execution space; do not depend on one identical worktree surviving forever.

## Shared state and locks

All manual and scheduled runs use the project's `.agent/TASK_STATE.json` and `.agent/LOCK.json`. A conflicting valid lock makes a scheduled run read-only. An expired lock can be cleared only after the recorded process is confirmed dead.

## Pause and terminal state

At `DONE`, set `automation_enabled=false` and pause the continuation task through the official scheduler UI when available. At `BLOCKED`, retain a low-noise condition check only when the task is configured for that purpose.
