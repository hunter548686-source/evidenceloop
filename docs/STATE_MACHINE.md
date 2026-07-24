# State Machine

## States

| State | Meaning | Typical next states |
|---|---|---|
| `INIT` | Goal registered, not yet reconciled with reality | `INSPECTING`, `BLOCKED` |
| `INSPECTING` | Filesystem, Git, runtime, dependencies and claims under review | `RESEARCH_NEEDED`, `PLANNING`, `VERIFYING`, `BLOCKED` |
| `RESEARCH_NEEDED` | A concrete external fact is missing or stale | `RESEARCHING`, `BLOCKED` |
| `RESEARCHING` | Authoritative sources are being collected | `FACT_CHECKING`, `RESEARCH_NEEDED`, `BLOCKED` |
| `FACT_CHECKING` | Adopted source claims are being validated locally | `PLANNING`, `EXECUTING`, `RESEARCH_NEEDED`, `BLOCKED` |
| `PLANNING` | Smallest verifiable action, rollback and acceptance are defined | `EXECUTING`, `RESEARCH_NEEDED`, `REPLANNING`, `BLOCKED` |
| `EXECUTING` | One bounded action is running | `VERIFYING`, `REPAIRING`, `RESEARCH_NEEDED`, `REPLANNING`, `BLOCKED` |
| `VERIFYING` | Original acceptance is being run and evidenced | `DONE`, `REPAIRING`, `REPLANNING`, `RESEARCH_NEEDED`, `BLOCKED` |
| `REPAIRING` | Root cause is tested and minimum repair applied | `VERIFYING`, `REPLANNING`, `RESEARCH_NEEDED`, `BLOCKED` |
| `REPLANNING` | Failed strategy is retired and a materially different route selected | `PLANNING`, `RESEARCH_NEEDED`, `BLOCKED` |
| `DONE` | All mandatory acceptance passed; read-only terminal state | none |
| `BLOCKED` | A concrete non-self-service condition prevents safe progress | `INSPECTING` after the condition changes |

## Prohibited success shortcuts

```text
PLANNING → DONE
EXECUTING → DONE
REPAIRING → DONE
```

The implementation rejects any transition not present in the canonical table. Only `VERIFYING → DONE` can succeed, and the checker evaluates every mandatory acceptance value before writing state.

## RESEARCH_APPLIED event

`RESEARCH_APPLIED` is not in the state enum. It is an audit event appended to `RESEARCH_LOG.md` and `DECISION_LOG.md` after a source-backed conclusion influences execution.

## Failure route

```text
EXECUTING/VERIFYING
  → first identical failure: REPAIRING
  → second identical failure: REPAIRING with root-cause re-check
  → third identical failure: REPLANNING and retire strategy
  → three distinct retired strategies with no safe route: BLOCKED
```

## Terminal invariants

### DONE

- `stop_reason` equals `acceptance_passed`.
- `automation_enabled` is false.
- `next_action` is read-only evidence preservation.
- `run_once` does not modify the project.

### BLOCKED

- `stop_reason` names a concrete condition.
- `next_action` is a condition check, not a retry.
- unchanged runs do not modify state or append duplicate reports.
- the only transition out is a new `INSPECTING` pass after the condition changes.

## Validation command

```bash
python3 scripts/validate_state.py --project "/absolute/path/to/project"
```

The validator checks required keys, types, enum membership, counters, terminal invariants, and acceptance constraints without requiring third-party packages.
