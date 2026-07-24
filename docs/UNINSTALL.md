# Uninstall

## Remove project integration but preserve state/evidence

```bash
python3 scripts/uninstall.py --project "/absolute/path/to/project"
```

Default behavior:

- removes `.agents/skills/autonomous-completion-loop/`;
- removes exactly one managed `AGENTS.md` block;
- preserves all pre-existing `AGENTS.md` instructions;
- preserves `.agent/` state, logs, rollback and evidence.

## Remove only the project Skill

```bash
python3 scripts/uninstall.py \
  --project "/absolute/path/to/project" \
  --keep-managed-block
```

## Remove only the managed AGENTS block

```bash
python3 scripts/uninstall.py \
  --project "/absolute/path/to/project" \
  --keep-project-skill
```

## Completely remove project state

```bash
python3 scripts/uninstall.py \
  --project "/absolute/path/to/project" \
  --remove-state
```

This is intentionally opt-in because `.agent/` contains audit and rollback evidence. Review or archive it first.

## Remove only the user/global Skill

```bash
python3 scripts/uninstall.py \
  --project "/absolute/path/to/project" \
  --keep-project-skill \
  --keep-managed-block \
  --remove-global-skill
```

Default global Skill path:

```text
~/.agents/skills/autonomous-completion-loop/
```

## Scheduled Tasks

Uninstalling files does not silently delete native Codex Scheduled Tasks. Pause or delete `Autonomous Project Continuation` and `Daily Autonomous Project Audit` in the official Scheduled Tasks UI before full removal.

## Verify preservation

```bash
git -C "/absolute/path/to/project" status --short
grep -c "AUTONOMOUS_COMPLETION_LOOP:START" "/absolute/path/to/project/AGENTS.md"
```

The test suite verifies that unrelated project files and pre-existing `AGENTS.md` text survive uninstall.
