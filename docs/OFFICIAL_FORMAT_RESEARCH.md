# Official Codex Format Research

Retrieved: **2026-07-23 (Australia/Sydney)**

Only official OpenAI documentation and the official OpenAI GitHub organization were used for adopted format decisions.

## 1. User and repository Skills

Source: https://learn.chatgpt.com/docs/build-skills

Confirmed:

- A Skill is a directory with a required `SKILL.md`.
- `SKILL.md` front matter includes at least `name` and `description`.
- Optional directories include scripts, references and assets.
- Codex supports explicit invocation with `$skill-name` and implicit invocation based on the description.
- The current user-level discovery directory is `$HOME/.agents/skills`.
- Repository-level Skills are discovered under `.agents/skills`.

Local validation:

- Existing skills were discovered under both `~/.agents/skills` and legacy/local `~/.codex/skills` on this machine.
- This implementation uses the current official user path `~/.agents/skills` and repository path `.agents/skills`.

## 2. AGENTS.md behavior

Source: https://learn.chatgpt.com/docs/agent-configuration/agents-md

Confirmed:

- Codex reads `AGENTS.md` before project work.
- User-level and repository-level instruction scopes can coexist.
- More specific project instructions take precedence over broader instructions.

Implementation decision:

- The installer never overwrites existing project instructions.
- It updates exactly one managed block using stable start/end markers.
- Repeated installation is idempotent.

## 3. Scheduled Tasks / Automations

Source: https://learn.chatgpt.com/docs/automations

Confirmed:

- Local project tasks can run against a project directory and may use an isolated worktree.
- Local execution requires the machine to be powered on, the Codex desktop application running, and the folder available.
- Scheduled Task management is provided through ChatGPT web or the Codex desktop application, not a management interface in Codex CLI or IDE.
- A web task cannot access a local project folder.

Local validation:

- Codex desktop applications are installed in `/Applications`.
- No supported `codex` executable was available in this session's PATH.
- Therefore the two required task definitions and prompts are fully prepared, but concrete native task creation and IDs cannot be truthfully claimed from this execution environment.

Result: `AUTOMATION_SETUP_REQUIRED`.

## 4. Worktrees

Source: https://learn.chatgpt.com/docs/environments/git-worktrees

Confirmed:

- Codex desktop can create isolated worktrees for tasks.
- Worktrees are separate working copies and can have detached or isolated state.

Conservative implementation inference:

- A single identical scheduler worktree is not used as the cross-run state authority.
- Durable checkpoints live in the target project's `.agent/` directory and every manual or scheduled writer uses the same `.agent/LOCK.json` protocol.

## 5. Official Codex repository

Source: https://github.com/openai/codex

Use:

- Official implementation and release reference only.
- No remote script was piped to a shell.
- Repository behavior must be inspected at a pinned revision before future code is borrowed.

## Adopted local format

```text
~/.agents/skills/autonomous-completion-loop/
  SKILL.md
  scripts/
  references/
  assets/

<project>/
  AGENTS.md
  .agents/skills/autonomous-completion-loop/
  .agent/
```

## Refresh rule

The source registry default freshness window is 30 days. Re-check these pages before adopting changed Codex formats, scheduler behavior, or directory conventions.
