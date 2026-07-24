# Installation

## Prerequisites

- macOS, Linux, or Windows with Python 3.11 or newer.
- Git for repository evidence.
- Codex desktop when local Scheduled Tasks are required.
- No third-party Python package is required.

## Verify the runtime

From a local checkout:

```bash
cd /absolute/path/to/evidenceloop
python3 -m compileall acl_loop scripts tests
python3 scripts/run_test_suite.py
```

## Install the package

From a local checkout:

```bash
python3 -m pip install .
evidenceloop --help
```

EvidenceLoop v0.1.0 is not published to PyPI. Installation therefore uses a source checkout or a Git URL. The package includes the project templates, schemas, policies, and Codex Skill assets required by its installation commands.

## Install the user Skill

```bash
evidenceloop install-global-skill
```

Default destination:

```text
~/.agents/skills/autonomous-completion-loop/
```

The installer copies `SKILL.md`, scripts, references and assets. Re-running it updates the same managed directory rather than creating a duplicate.

## Install into a Git project

```bash
evidenceloop install-project \
  --project "/absolute/path/to/project" \
  --goal "The exact project goal"
```

Allowed installation changes:

```text
.agent/
.agents/skills/autonomous-completion-loop/
AGENTS.md managed block only
```

The installer never overwrites pre-existing instructions. It appends or updates exactly one block bounded by:

```text
<!-- AUTONOMOUS_COMPLETION_LOOP:START -->
<!-- AUTONOMOUS_COMPLETION_LOOP:END -->
```

Before changing an existing `AGENTS.md`, it saves a copy under `.agent/EVIDENCE/rollback-before-install-<timestamp>/`.

## Validate installation

```bash
evidenceloop validate-state --project "/absolute/path/to/project"
evidenceloop inspect --project "/absolute/path/to/project"
evidenceloop acceptance --project "/absolute/path/to/project"
```

Installation does not mark a business product complete. Its initial goal is limited to proving that the loop is installed, resumable, evidence-backed, and did not change business code.

## Editable source installation

Optional for contributors:

```bash
python3 -m pip install -e .
```

The backward-compatible `acl-loop` command remains available in v0.1.0.
