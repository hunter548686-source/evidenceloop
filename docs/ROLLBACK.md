# Rollback

## Remove a project installation

Default safe rollback preserves `.agent/` evidence:

```bash
evidenceloop uninstall --project "/absolute/path/to/project"
```

Complete state removal is opt-in:

```bash
evidenceloop uninstall --project "/absolute/path/to/project" --remove-state
```

Before changing an existing `AGENTS.md`, the installer stores its rollback copy under `.agent/EVIDENCE/rollback-before-install-<timestamp>/AGENTS.md`. Restore that copy only when a byte-for-byte rollback is required.

## Remove the user Skill

Remove only the managed user Skill directory:

```text
~/.agents/skills/autonomous-completion-loop/
```

Do not remove another project's `.agent/` state or `AGENTS.md` content manually. Use the conservative uninstaller and review its result.

## Release rollback

If a release is defective, preserve the published tag and release record, document the defect, and publish a corrected version. Deleting or moving a public release tag destroys evidence and is not the default rollback method.
