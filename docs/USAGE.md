# Usage

## Three simplest Codex calls

```text
$autonomous-completion-loop 开始执行这个任务直到完成。

$autonomous-completion-loop 读取 TASK_STATE，从 next_action 继续。

$autonomous-completion-loop 检查这个项目为什么停止，并恢复执行。
```

## Inspect current state

```bash
python3 scripts/validate_state.py --project "/absolute/path/to/project"
python3 scripts/select_next_action.py --project "/absolute/path/to/project"
python3 scripts/generate_status_report.py --project "/absolute/path/to/project"
```

The status report writes `.agent/EVIDENCE/latest-status-report.json` and appends a concise human-readable record to `AUTOMATION_REPORT.md`.

## Run one controlled cycle

```bash
python3 scripts/run_once.py --project "/absolute/path/to/project" --owner "manual-codex-session"
```

This acquires the shared lock, inspects the project, updates the checkpoint, writes a report, and releases the lock. It refuses to modify `DONE` or `BLOCKED` work.

## View and change state

```bash
python3 scripts/transition_state.py \
  --project "/absolute/path/to/project" \
  --to INSPECTING \
  --reason "Starting evidence-backed inspection" \
  --next-action "Verify repository entrypoints and current test state."
```

To enter `DONE`, the current state must be `VERIFYING` and every mandatory acceptance item must already be true.

## Record a failure

```bash
python3 scripts/record_failure.py \
  --project "/absolute/path/to/project" \
  --category "测试错误" \
  --strategy "focused-unit-test-repair" \
  --error "actual command output" \
  --root-cause-hypothesis "bounded hypothesis" \
  --experiment "smallest experiment that distinguishes the hypothesis" \
  --repair "minimum proposed repair"
```

The third identical failure retires the strategy and enters `REPLANNING`. Three distinct failed strategies can enter `BLOCKED` only with a concrete unblock condition.

## Lock operations

```bash
python3 scripts/manage_lock.py --project "/absolute/path/to/project" status
python3 scripts/manage_lock.py --project "/absolute/path/to/project" acquire --owner manual --operation verify
python3 scripts/manage_lock.py --project "/absolute/path/to/project" release --run-id "returned-run-id"
python3 scripts/manage_lock.py --project "/absolute/path/to/project" recover
```

Never delete `LOCK.json` blindly. Recovery succeeds only when the lock is expired and the recorded process is not alive.

## Pause Automation

Open the official Scheduled Tasks/Automations interface in Codex desktop or ChatGPT web, select `Autonomous Project Continuation`, and pause or disable it. Also set `automation_enabled` to `false` only through a validated state change or `DONE` transition; do not edit an active state casually.

## Re-enable Automation

Validate project state and lock first, then re-enable the Scheduled Task in the official UI. Resume from `next_action`; do not create a second task with the same purpose unless the original task is absent.

## View `next_action`

```bash
python3 scripts/select_next_action.py --project "/absolute/path/to/project"
```

## Judge `DONE`

`DONE` requires:

1. current state was `VERIFYING`;
2. every mandatory `acceptance_results` value is true;
3. the transition checker accepted the move;
4. `stop_reason` is `acceptance_passed`;
5. no further modification occurs.

## Handle `BLOCKED`

Read `stop_reason`, the latest failure record, and `next_action`. Check only the named external unblock condition. If unchanged, do not rerun the same command or append a duplicate report.

## Archive a completed run

```bash
python3 scripts/archive_completed_run.py --project "/absolute/path/to/project"
```

Only a `DONE` run can be archived.

## Mac sleep, shutdown, or Codex not running

Local Scheduled Tasks do not run while the Mac is powered off, the required local folder is unavailable, or the Codex desktop application is not running. The next run must validate the state and resume from `next_action`; it must not assume missed intervals executed.
