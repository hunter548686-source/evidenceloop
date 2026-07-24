# Security

## Default-deny operations

The loop does not authorize:

- reading, displaying, copying or logging secrets;
- Git commit, push or merge;
- release publication or production deployment;
- paid purchases or account changes;
- deletion of user data;
- irreversible database operations;
- modification of important files outside authorized project and Skill paths;
- reduction of operating-system security controls.

## Project inspection

`inspect_project` reads directory entries, file metadata, project markers and Git output. It does not read file contents during general inspection and explicitly flags secret-like names such as `.env`, credential, password, token, secret and private-key files.

The report includes:

```json
{
  "security": {
    "secret_file_contents_read": false,
    "inspection_policy": "metadata and Git evidence only"
  }
}
```

## External code

Never run a remote shell stream. Public code must be saved locally, inspected, version-pinned where possible, and tested in a disposable environment before adoption.

## Concurrency

Manual sessions and Scheduled Tasks share `.agent/LOCK.json`. A valid lock blocks a second writer. A conflicting session may inspect read-only. Expired-lock recovery also checks process liveness.

## Managed-file scope

The project installer changes only:

- `.agent/` state and evidence;
- `.agents/skills/autonomous-completion-loop/`;
- one delimited block in `AGENTS.md`.

Existing `AGENTS.md` content is preserved and backed up before the first managed change. The default uninstaller leaves `.agent/` evidence intact.

## Static safety verification

The test suite scans executable Python and shell files for forbidden command patterns, including Git push/merge and remote pipe-to-shell patterns. This does not replace code review, but it prevents accidental inclusion in the delivered runtime.

## No secret test data

Tests create disposable repositories with synthetic marker files. A synthetic `.env` sentinel verifies that inspection does not copy or reveal its contents.
