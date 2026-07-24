# Acceptance

`DONE` is prohibited until every mandatory machine-readable item in `TASK_STATE.json.acceptance_results` is `true`.

## Mandatory checks

- [ ] `state_schema_valid` — state exists and passes deterministic validation.
- [ ] `project_skill_installed` — `.agents/skills/autonomous-completion-loop/SKILL.md` exists.
- [ ] `managed_agents_block_valid` — exactly one managed block exists without replacing prior instructions.
- [ ] `security_boundaries_verified` — no secret content read and no commit/push/merge/release/deploy action performed.
- [ ] `relevant_tests_passed` — the required test, lint, type, build, or focused verification commands passed.
- [ ] `evidence_complete` — commands, outputs, exit codes, timestamps, results, and rollback evidence are stored.

The acceptance checker reads machine state; this Markdown file documents the contract and must not be used to bypass failed machine results.
