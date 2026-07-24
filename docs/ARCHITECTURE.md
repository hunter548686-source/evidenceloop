# Architecture

## System context

EvidenceLoop is a local control plane between a user goal, a real Git project, Codex interactive or scheduled execution, official external sources, and deterministic project evidence.

```text
User goal
  │
  ▼
Codex Skill ──────── official research sources
  │                          │
  ▼                          ▼
acl_loop control package ─ source validation/freshness
  │
  ├── .agent task state, logs, lock, evidence
  ├── .agents/skills project Skill
  ├── AGENTS.md managed instructions
  └── real project files, Git, dependencies, tests
```

## Components

| Component | Authority | Responsibility |
|---|---|---|
| `acl_loop/core.py` | Behavior | State validation, transition gate, failure policy, sources, locks, installer, inspection, reports, archive |
| `acl_loop/cli.py` | Interface | Stable JSON command interface and exit codes |
| `scripts/` | Entry points | Required task-specific wrappers and test evidence runner |
| `.agent/TASK_STATE.json` | Run state | Current status, strategy, retries, acceptance, next action, terminal reason |
| `.agent/LOCK.json` | Concurrency | Shared manual/Automation write lock with expiry and process identity |
| `.agent/EVIDENCE/` | Proof | Inspections, command results, acceptance and rollback evidence |
| `SOURCE_REGISTRY.json` | External facts | Adopted claims with real URLs, dates, versions, limitations and local validation |
| Skill | Agent protocol | Explicit and semantic activation, safe execution loop |
| `schedule-policy.yaml` | Scheduler configuration | Names, cadence, timezone, full prompts and local availability assumptions |

## Persistence and recovery

State and JSON outputs use atomic replace. `next_action` is the resume checkpoint. A scheduler worktree is not treated as the only durable state because it may be isolated or replaced; project `.agent/` is the durable authority.

## Acceptance gate

The transition table forbids direct success from planning, execution, or repair. Only `VERIFYING → DONE` is legal, after all mandatory acceptance results are true. `DONE` disables modification. `BLOCKED` requires a concrete stop reason and a minimum unblock condition.

## Failure control

Failures are fingerprinted by strategy, category and normalized error. The first occurrence enters repair, the second forces root-cause re-evaluation, and the third retires that strategy into replanning. Three distinct retired strategies lead to `BLOCKED` only when no safe self-service route remains.

## Security design

Project inspection reads metadata and Git evidence, not secret-like file contents. No implementation path invokes commit, push, merge, release, production deployment, paid service, or destructive data operation. Install and uninstall are limited to managed paths and preserve pre-existing `AGENTS.md` content.
