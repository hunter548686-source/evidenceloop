# Recovery

## Recover after an interrupted conversation or task

1. Read applicable `AGENTS.md` and the installed Skill.
2. Validate `.agent/TASK_STATE.json`.
3. Inspect real Git and filesystem state; do not trust the last prose report by itself.
4. Read the latest `PROGRESS.md`, `FAILURE_LOG.md`, `AUTOMATION_REPORT.md`, and evidence files.
5. Check `.agent/LOCK.json`.
6. Reconcile partial output against the last recorded acceptance command.
7. Acquire the lock and continue from the smallest valid `next_action`.

```bash
python3 scripts/validate_state.py --project "/absolute/path/to/project"
python3 scripts/manage_lock.py --project "/absolute/path/to/project" status
python3 scripts/select_next_action.py --project "/absolute/path/to/project"
```

## Expired lock recovery

Do not delete the lock file manually. Run:

```bash
python3 scripts/manage_lock.py --project "/absolute/path/to/project" recover
```

Recovery is permitted only when:

- `expires_at` is in the past; and
- the recorded `owner_pid` is not alive.

A timestamp-expired lock with a live process is not removed. Recovery is recorded in `AUTOMATION_REPORT.md`.

## Failed strategy recovery

Read the failure fingerprint and count. The third identical failure retires that strategy. A replanned route must be materially different and supported by new evidence; changing command spelling without changing the hypothesis is not a new strategy.

## State corruption

If JSON is invalid:

- preserve the corrupt file under `.agent/EVIDENCE/`;
- reconstruct only from verifiable logs, files, Git and command evidence;
- never infer completed tasks solely from prose;
- re-run acceptance before restoring `VERIFYING` or `DONE`.

## Scheduler gaps

When the Mac slept, was powered off, the folder was unavailable, or Codex desktop was not running, missed local intervals are not assumed to have executed. The next available run performs a full state/lock reconciliation and resumes from `next_action`.

## Completed-run archive

After evidence-backed `DONE`:

```bash
python3 scripts/archive_completed_run.py --project "/absolute/path/to/project"
```

The archive copies state, logs, sources, acceptance and handoff into `.agent/ARCHIVE/<timestamp>/` without recursively copying previous archives.
