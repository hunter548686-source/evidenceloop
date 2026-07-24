# Task Plan

## Goal

Use the exact goal in `TASK_STATE.json`. Do not broaden it without evidence and owner authority.

## Milestone contract

Every milestone must record:

- Objective
- Inputs and confirmed dependencies
- Files or systems allowed to change
- Acceptance criteria
- Verification command
- Rollback procedure
- Current result
- Evidence location

## Initial milestone — installation verification

- Objective: prove the completion loop is installed without changing business code.
- Inputs: repository metadata, `AGENTS.md`, project entry markers, Git state.
- Allowed changes: `.agent/`, `.agents/skills/autonomous-completion-loop/`, managed `AGENTS.md` block.
- Acceptance: mandatory installation checks pass and evidence is stored.
- Verification: `python3 /path/to/Codex\ Autonomous\ Completion\ Loop/scripts/validate_state.py --project <project>`.
- Rollback: remove the managed block and project Skill; restore the saved pre-install `AGENTS.md` copy when required.
- Evidence: `.agent/EVIDENCE/installation-result.json`.
