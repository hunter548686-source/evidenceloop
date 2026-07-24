# Examples

## Install into a disposable repository

```bash
tmp="$(mktemp -d)"
git init "$tmp"
python3 ../scripts/install_project_loop.py \
  --project "$tmp" \
  --goal "Create one verified local file and prove it with a focused test."
python3 ../scripts/validate_state.py --project "$tmp"
```

## Resume a project

```text
$autonomous-completion-loop 读取 TASK_STATE，从 next_action 继续。
```

The Agent validates the state, inspects the real project, acquires the lock, performs one smallest verifiable action, saves evidence, updates `next_action`, and releases the lock.

## Research event

A valid adopted research entry must include a real URL and local validation. Use `acl_loop.core.record_research_applied` only after the entry passes source validation. The event appears in both `RESEARCH_LOG.md` and `DECISION_LOG.md`, while the task remains in its normal execution state.

## Terminal examples

- A `DONE` project returns a read-only next action and `run_once` changes nothing.
- A `BLOCKED` project returns a condition-check-only next action and does not append duplicate reports.

See `sample-project-registry.json` for the portable registry shape.
