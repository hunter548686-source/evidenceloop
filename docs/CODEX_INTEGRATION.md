# Codex integration walkthrough

This walkthrough uses the public EvidenceLoop v0.1.0 tag to create a disposable Git repository with one intentionally failing test. It then installs the repository Skill, hands the repair goal to Codex, resumes from project state, and reviews the resulting evidence.

EvidenceLoop is the public project name. The Codex Skill identifier remains `autonomous-completion-loop` for compatibility, so explicit invocation uses `$autonomous-completion-loop`.

## Evidence boundary

Three different behaviors are involved:

1. EvidenceLoop CLI operations are deterministic and can be tested directly.
2. Codex interprets the goal and performs the project work; it must verify the result before entering `DONE`.
3. Scheduled Tasks are optional UI-managed automation. They are not required for this walkthrough.

`run-once` does not repair code or execute the project acceptance command. It acquires the lock, inspects metadata, updates a checkpoint, writes a report, and releases the lock. Likewise, `acceptance --set` records a Boolean gate supplied by the operator or agent; it does not independently prove that a test passed.

## 1. Create a disposable failing repository

Run these commands in one shell. They clone a fixed public tag because EvidenceLoop v0.1.0 is not published to PyPI.

```bash
export LAB_ROOT="$(mktemp -d)"
export RUNTIME="$LAB_ROOT/evidenceloop"
export DEMO="$LAB_ROOT/demo"

git clone --depth 1 --branch v0.1.0 \
  https://github.com/hunter548686-source/evidenceloop.git \
  "$RUNTIME"

mkdir -p "$DEMO/tests"
git -C "$DEMO" init -b main

cat > "$DEMO/.gitignore" <<'EOF'
.agent/
.env
.env.*
__pycache__/
EOF

cat > "$DEMO/answer.py" <<'PY'
def answer() -> int:
    return 1
PY

cat > "$DEMO/tests/test_answer.py" <<'PY'
import unittest

from answer import answer


class AnswerTest(unittest.TestCase):
    def test_answer(self) -> None:
        self.assertEqual(answer(), 2)


if __name__ == "__main__":
    unittest.main()
PY

git -C "$DEMO" add .gitignore answer.py tests/test_answer.py
git -C "$DEMO" \
  -c user.name="EvidenceLoop walkthrough" \
  -c user.email="walkthrough@example.invalid" \
  commit -m "Create disposable failing fixture"
```

The synthetic email uses the reserved `.invalid` domain and is not an owner identity.

Confirm the intended baseline failure:

```bash
(
  cd "$DEMO"
  python3 -B -m unittest discover -s tests -v
)
```

This first command is expected to exit nonzero because `answer()` deliberately returns the wrong value. That failure is demo input, not an EvidenceLoop installation failure.

## 2. Install the repository integration

Run the CLI with the sibling v0.1.0 checkout first on `PYTHONPATH`. Running from `$DEMO` makes `../evidenceloop` resolve to the fixed clone and prevents an unrelated installed `acl_loop` package from taking precedence.

```bash
(
  cd "$DEMO"
  PYTHONNOUSERSITE=1 PYTHONPATH="../evidenceloop" \
    python3 -m acl_loop.cli \
    install-project \
    --project "$DEMO" \
    --goal "Repair the disposable failing test and preserve evidence."
)
```

The installer creates project-local state under `.agent/`, copies the Skill to `.agents/skills/autonomous-completion-loop/`, and adds one managed EvidenceLoop block to `AGENTS.md`.

Verify the imported module path, state, and installed Skill:

```bash
(
  cd "$DEMO"
  PYTHONNOUSERSITE=1 PYTHONPATH="../evidenceloop" \
    python3 - <<'PY'
from pathlib import Path
import acl_loop

runtime = Path("../evidenceloop").resolve()
loaded = Path(acl_loop.__file__).resolve()
assert loaded.is_relative_to(runtime), (loaded, runtime)
print(f"pinned_runtime={loaded}")
PY

  PYTHONNOUSERSITE=1 PYTHONPATH="../evidenceloop" \
    python3 -m acl_loop.cli \
    validate-state \
    --project "$DEMO"
)

grep -n '^name: autonomous-completion-loop$' \
  "$DEMO/.agents/skills/autonomous-completion-loop/SKILL.md"

git -C "$DEMO" status --short
```

The state authority is `$DEMO/.agent/TASK_STATE.json`. The next action is the `next_action` field in that file, not a claim recovered from chat history.

## 3. Invoke Codex

Open the disposable `$DEMO` repository in Codex and send:

```text
$autonomous-completion-loop

Work only in this disposable repository.
Goal: repair the intentionally failing unittest.
EvidenceLoop CLI prefix for this lab:
PYTHONNOUSERSITE=1 PYTHONPATH="../evidenceloop" python3 -m acl_loop.cli
Acceptance command: python3 -B -m unittest discover -s tests -v

Validate TASK_STATE first, acquire .agent/LOCK.json before writes, record the
initial synthetic failure without reading secret files, apply the smallest
repair, rerun the original acceptance command, save command evidence, and
continue until evidence-backed DONE or a genuine BLOCKED condition.

Do not commit, push, publish, release, deploy, spend money, or perform
irreversible operations.
```

Codex should follow the installed Skill contract: inspect real state, acquire the project lock, work from `next_action`, record the failing acceptance result in `FAILURE_LOG.md`, make the minimum repair, rerun the same test, and enter `DONE` only from `VERIFYING` after every mandatory acceptance result is true.

The first recorded acceptance failure moves this demonstration to `REPAIRING`. After the minimum repair, Codex returns to `VERIFYING` and reruns the original command; it cannot skip directly from repair or execution to `DONE`.

The prompt is a goal and safety contract, not proof of completion. Verify the files and commands in the next section.

## 4. Resume from a later Codex session

If the session is interrupted, reopen the same disposable repository and send:

```text
$autonomous-completion-loop 读取 TASK_STATE，从 next_action 继续。
```

The new session must validate `.agent/TASK_STATE.json` and the shared lock before acting. It must not assume that a previous response or missed Scheduled Task interval completed the work.

## 5. Review the result and evidence

Use the same pinned source route for read-only state checks:

```bash
(
  cd "$DEMO"

  PYTHONNOUSERSITE=1 PYTHONPATH="../evidenceloop" \
    python3 -m acl_loop.cli validate-state --project "$DEMO"

  PYTHONNOUSERSITE=1 PYTHONPATH="../evidenceloop" \
    python3 -m acl_loop.cli next-action --project "$DEMO"

  PYTHONNOUSERSITE=1 PYTHONPATH="../evidenceloop" \
    python3 -m acl_loop.cli acceptance --project "$DEMO"

  python3 -B -m unittest discover -s tests -v
)

git -C "$DEMO" status --short
git -C "$DEMO" diff -- answer.py
```

Review `.agent/TASK_STATE.json`, `.agent/PROGRESS.md`, `.agent/FAILURE_LOG.md`, and the command records under `.agent/EVIDENCE/`. Do not read `.env`, credential, token, key, recovery, or other secret-like file contents.

Do not use `report` or `inspect` as post-`DONE` read-only checks: in an installed project they can write report or inspection evidence. Preserve a `DONE` project without further loop mutation.

`inspect` reports Git and top-level metadata and marks secret-like names without reading those file contents. It is not a whole-repository secret scanner.

## 6. Failure and lock recovery

Failure records should contain only the minimum redacted error summary needed to reproduce the failure. Never copy a credential, environment-file value, private key, or recovery value into `record-failure`, logs, prompts, or evidence.

Check lock state without deleting the lock file:

```bash
(
  cd "$DEMO"
  PYTHONNOUSERSITE=1 PYTHONPATH="../evidenceloop" \
    python3 -m acl_loop.cli lock --project "$DEMO" status
)
```

Use `lock recover` only when the recorded expiry has passed and the recorded process is no longer alive. An active conflicting lock makes the run read-only.

## 7. Rollback

Before the task reaches `DONE`, first pause the active Codex run and any Codex desktop local-project Scheduled Task for this demo. Check the lock and proceed only when it reports `"valid": false` with no active run ID. Do not uninstall underneath a live writer.

```bash
(
  cd "$DEMO"
  set -e

  lock_status="$(
    PYTHONNOUSERSITE=1 PYTHONPATH="../evidenceloop" \
      python3 -m acl_loop.cli lock --project "$DEMO" status
  )"
  printf '%s\n' "$lock_status"

  LOCK_STATUS_JSON="$lock_status" python3 - <<'PY'
import json
import os
import sys

payload = json.loads(os.environ["LOCK_STATUS_JSON"])
run_id = payload.get("data", {}).get("run_id")
if payload.get("ok") is not True or payload.get("valid") or run_id:
    print("Refusing uninstall: pause writers and clear the active lock first.", file=sys.stderr)
    raise SystemExit(1)
PY

  rollback_run_id="$(
    python3 - <<'PY'
import uuid

print(uuid.uuid4())
PY
  )"
  rollback_lock_acquired=false
  release_rollback_lock() {
    if [ "$rollback_lock_acquired" = true ]; then
      PYTHONNOUSERSITE=1 PYTHONPATH="../evidenceloop" \
        python3 -m acl_loop.cli \
        lock --project "$DEMO" release --run-id "$rollback_run_id"
    fi
  }
  trap release_rollback_lock EXIT

  PYTHONNOUSERSITE=1 PYTHONPATH="../evidenceloop" \
    python3 -m acl_loop.cli \
    lock --project "$DEMO" acquire \
    --owner "evidenceloop-rollback" \
    --operation "rollback-uninstall" \
    --ttl-minutes 10 \
    --run-id "$rollback_run_id"
  rollback_lock_acquired=true

  PYTHONNOUSERSITE=1 PYTHONPATH="../evidenceloop" \
    python3 -m acl_loop.cli uninstall --project "$DEMO"

  PYTHONNOUSERSITE=1 PYTHONPATH="../evidenceloop" \
    python3 -m acl_loop.cli \
    lock --project "$DEMO" release --run-id "$rollback_run_id"
  rollback_lock_acquired=false
  trap - EXIT
)
```

The acquisition closes the gap between the initial status check and the uninstall write. If another writer acquires a lock in that interval, this rollback acquisition fails and `set -e` stops before uninstall. The default uninstall removes the project Skill and managed `AGENTS.md` block while preserving `.agent/` evidence and user files. `--remove-state` is intentionally separate and should be used only for a disposable repository whose evidence is no longer needed. See the [uninstall guide](UNINSTALL.md) for the full boundary.

After `DONE`, keep the loop state read-only. If the disposable lab is no longer needed, preserve any evidence you want and remove the entire lab outside the EvidenceLoop run rather than mutating a completed state.

## 8. Optional Scheduled Tasks

Scheduled Tasks are optional. For this local `$DEMO` folder, execution must use a Codex desktop local-project task; a ChatGPT web task cannot access the local folder. Local execution also requires the machine to be powered on, the Codex desktop app running, and the project folder available.

The status remains `AUTOMATION_SETUP_REQUIRED` until a supported local task is created and its real operation is verified in the official UI. This walkthrough does not claim that a Scheduled Task was created or that unattended execution was verified. See [automation setup](AUTOMATION_SETUP.md) for the prepared prompts and current limitations.

## What this walkthrough proves

When the commands and acceptance checks pass, they prove the local installation, state transitions, failure-repair evidence, and final acceptance for this disposable example. A green CI run proves only that the configured commands passed in the listed jobs. It does not prove output quality, production readiness, security certification, adoption, or external users.

For broader setup details, see [installation](INSTALLATION.md), [usage](USAGE.md), and [recovery](RECOVERY.md).
