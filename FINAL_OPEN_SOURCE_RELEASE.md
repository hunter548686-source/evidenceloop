# EvidenceLoop Initial Open-Source Release Handoff

## Final status

**DONE**

The public repository, `main` branch, initial release commit, `v0.1.0` tag and GitHub Release, community files, five maintainer-created roadmap Issues, release verification, and OpenAI application materials all have live evidence.

The OpenAI application form was **not submitted**. Owner-only account fields remain required.

## GitHub publication

- GitHub username: `hunter548686-source`
- Repository: https://github.com/hunter548686-source/evidenceloop
- Visibility: `PUBLIC`
- Default branch: `main`
- Repository description: `A fail-closed evidence and conformance protocol for coding agents.`
- Release: https://github.com/hunter548686-source/evidenceloop/releases/tag/v0.1.0
- Release title: `EvidenceLoop v0.1.0`
- Tag: `v0.1.0`
- Release commit: `94eecaffa0d257c93a77df5a7be61f77433e15af`
- Application-evidence commit: `d564b948e4ee24167e79d3e8ebd1b9c9c50addda`
- License recognized by GitHub: `Apache-2.0`
- Private vulnerability reporting: enabled

## Verification

| Command or check | Result |
|---|---|
| `python3 -m compileall acl_loop scripts tests` | Exit 0 |
| `python3 scripts/run_test_suite.py` | Exit 0; 25/25 passed |
| `python3 -m pip install --no-deps --target <temporary-target> .` | Exit 0; EvidenceLoop 0.1.0 wheel built and installed |
| Installed-package `python3 -m acl_loop.cli --help` | Exit 0 |
| Installed-package global Skill installation | Exit 0 |
| Installed-package disposable-project installation | Exit 0 |
| `pyproject.toml` parse | Pass: `evidenceloop` 0.1.0 |
| Four JSON schemas parse | Pass |
| Three GitHub Issue Form YAML files parse | Pass |
| Local Markdown link validation | Pass; zero missing targets |
| `git diff --check` | Exit 0 |
| Staged release `git diff --cached --check` | Exit 0 |

Test count: **25**.

The installed-only smoke ran outside the source checkout, proving that the wheel's packaged templates, schemas, policies, and Skill assets are used successfully.

## Public file inventory

The `v0.1.0` tag contains **108 files**:

| Area | Files | Purpose |
|---|---:|---|
| Root | 11 | README, license, governance, security, roadmap, metadata, and project rules |
| `.agents/` | 6 | Repository-discoverable Codex Skill mirror |
| `.github/` | 4 | Bug/feature Issue Forms, Issue configuration, and pull-request template |
| `acl_loop/` | 29 | Runtime and packaged resources |
| `config/` | 4 | Default, research, safety, and schedule policies |
| `docs/` | 13 | Architecture, operation, recovery, release, and application draft documentation |
| `examples/` | 2 | Public examples |
| `schemas/` | 4 | Versioned JSON Schemas |
| `scripts/` | 16 | Stable source-checkout entrypoints and test runner |
| `skill/` | 6 | Canonical Codex Skill source |
| `templates/` | 12 | Project installation templates |
| `tests/` | 1 | 25-test conformance-oriented suite |

After the release tag, `main` adds the copy-ready OpenAI application handoff and this final release report.

## Safety scan

The complete 108-file release candidate was scanned before commit:

- secret-like filenames: 0;
- internal artifact paths: 0;
- machine or owner absolute paths: 0;
- private-key blocks: 0;
- email addresses: 0;
- Chinese password term: 0;
- named private business projects: 0;
- previous public project name: 0.

Two generic assignment-pattern matches were reviewed. One is the secret-name detector variable; the other is a synthetic `.env` non-disclosure test. Neither contains a credential.

Ignored and not published: `.agent/`, `.pbos/`, `tests/results/`, the root internal handoff, internal blueprint files, delivery inventory, caches, build output, and package metadata.

## Public Issues

All are maintainer-created roadmap work, not external-user feedback:

1. [Add Codex integration walkthrough](https://github.com/hunter548686-source/evidenceloop/issues/1)
2. [Add generic CLI adapter example](https://github.com/hunter548686-source/evidenceloop/issues/2)
3. [Design conformance test levels](https://github.com/hunter548686-source/evidenceloop/issues/3)
4. [Define Evidence Bundle manifest v0.1](https://github.com/hunter548686-source/evidenceloop/issues/4)
5. [Add GitHub Actions CI matrix for Python 3.11–3.13](https://github.com/hunter548686-source/evidenceloop/issues/5)

The GitHub API confirmed all five repaired Issue bodies exactly match their intended Roadmap text.

## OpenAI application materials

- [Application draft](docs/OPENAI_APPLICATION_DRAFT.md)
- [Copy-ready application handoff](docs/OPENAI_APPLICATION_READY.md)
- Official form: https://openai.com/form/codex-for-oss/

Owner input still required:

- first name;
- last name;
- email associated with the owner's ChatGPT account;
- OpenAI Organization ID;
- final support-checkbox choice;
- owner review and form submission.

No owner-only value was inferred from GitHub or local files.

## Known limitations

- EvidenceLoop v0.1.0 is alpha software.
- It is not published to PyPI; installation uses a source checkout or Git URL.
- The Python 3.11–3.13 GitHub Actions matrix is roadmap work.
- Evidence Bundle manifest v0.1 and formal conformance levels are not yet defined.
- Scheduled Task creation still requires the supported Codex or ChatGPT interface.
- The compatibility Skill identifier `autonomous-completion-loop` and command `acl-loop` remain in v0.1.0.
- No stars, downloads, external users, external feedback, or ecosystem adoption are claimed.

## Corrected failures

No failure remains unexplained:

- A research-record enum mismatch was corrected and the official-source registry passed.
- The system Ruby 2.6 YAML validation command was adapted to its supported Psych API.
- Shell substitution malformed the first Issue bodies and unintentionally reran the test suite; all five bodies were replaced from literal files and verified exactly through the GitHub API.
- A Python f-string scan syntax error was corrected without changing the application documents.
- A zsh `path` variable invalidated one remote-check attempt; its empty-value results were discarded, and the complete check was rerun with non-empty SHA assertions.

## Rollback

- Preserve the public `v0.1.0` tag and Release as historical evidence.
- For a defect, fix forward on `main` and publish a corrected patch release rather than deleting or moving the tag.
- Inspect the immutable release in a disposable worktree with `git worktree add <temporary-directory> v0.1.0`.
- A pre-edit local snapshot and the prior completed-run archive are recorded in ignored internal evidence. Retain the temporary snapshot until 2026-07-31, then remove it if no restoration is needed.
- Repository deletion, visibility reversal, or release deletion was not performed and requires separate owner authorization.

## Next recommendation

Do not submit the OpenAI form today. First close the CI-matrix Issue, publish the Codex integration walkthrough, and complete at least one visible follow-up maintenance cycle. Then refresh the live counts, supply the owner-only fields, and submit the application.
