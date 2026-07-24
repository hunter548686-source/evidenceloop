from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from acl_loop import core

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "tests" / "results"


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_fingerprint(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and ".git" not in path.parts:
            result[str(path.relative_to(root))] = file_hash(path)
    return result


def source_entry(url: str = "https://example.com/official") -> dict[str, object]:
    return {
        "question": "What format applies?",
        "claim": "The verified format applies.",
        "source_title": "Official reference",
        "source_url": url,
        "publisher": "Example Standards Body",
        "source_type": "official_documentation",
        "published_at": None,
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "applicable_version": "1.0",
        "evidence_summary": "A bounded primary-source conclusion.",
        "confidence": "high",
        "local_validation": "passed",
        "limitations": "Synthetic test entry.",
    }


class CompletionLoopTestCase(unittest.TestCase):
    temp_records: list[dict[str, object]] = []

    def setUp(self) -> None:
        self.temp_path = Path(tempfile.mkdtemp(prefix="acl-loop-test-"))
        completed = subprocess.run(
            ["git", "init", "-q", str(self.temp_path)],
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.record = {
            "path": str(self.temp_path),
            "created": True,
            "git_initialized": True,
            "cleaned": False,
        }

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_path, ignore_errors=True)
        self.record["cleaned"] = not self.temp_path.exists()
        self.temp_records.append(self.record)

    @classmethod
    def tearDownClass(cls) -> None:
        RESULTS.mkdir(parents=True, exist_ok=True)
        (RESULTS / "temporary-repositories.json").write_text(
            json.dumps(cls.temp_records, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def install(self, goal: str = "Verify governed installation") -> dict[str, object]:
        return core.install_project(self.temp_path, goal=goal)

    def move_to_executing(self) -> None:
        core.transition_state(self.temp_path, "INSPECTING", reason="real inspection started")
        core.transition_state(self.temp_path, "PLANNING", reason="smallest action selected")
        core.transition_state(self.temp_path, "EXECUTING", reason="bounded action started")

    def move_to_verifying(self) -> None:
        self.move_to_executing()
        core.transition_state(self.temp_path, "VERIFYING", reason="original acceptance running")

    def mark_all_acceptance(self) -> dict[str, bool]:
        return {name: True for name in core.MANDATORY_ACCEPTANCE}

    def test_01_fresh_git_project_installation(self) -> None:
        result = self.install()
        self.assertTrue((self.temp_path / ".agent" / "TASK_STATE.json").exists())
        self.assertTrue((self.temp_path / ".agents" / "skills" / "autonomous-completion-loop" / "SKILL.md").exists())
        self.assertEqual(result["business_code_modified"], False)
        self.assertEqual((self.temp_path / "AGENTS.md").read_text(encoding="utf-8").count(core.MANAGED_START), 1)

    def test_02_existing_agents_project_installation_preserves_content(self) -> None:
        original = "# Existing Rules\n\nKeep this exact instruction.\n"
        (self.temp_path / "AGENTS.md").write_text(original, encoding="utf-8")
        result = self.install()
        installed = (self.temp_path / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn(original.strip(), installed)
        self.assertIn(core.MANAGED_START, installed)
        rollback = Path(str(result["rollback_dir"])) / "AGENTS.md"
        self.assertEqual(rollback.read_text(encoding="utf-8"), original)

    def test_03_repeated_installation_is_idempotent(self) -> None:
        self.install()
        self.install()
        agents = (self.temp_path / "AGENTS.md").read_text(encoding="utf-8")
        self.assertEqual(agents.count(core.MANAGED_START), 1)
        self.assertEqual(agents.count(core.MANAGED_END), 1)
        self.assertTrue((self.temp_path / ".agents" / "skills" / "autonomous-completion-loop" / "SKILL.md").exists())

    def test_04_state_validation(self) -> None:
        self.install()
        self.assertEqual(core.validate_state_file(self.temp_path), [])
        state_path = self.temp_path / ".agent" / "TASK_STATE.json"
        state = core.read_json(state_path)
        del state["goal"]
        core.atomic_write_json(state_path, state)
        errors = core.validate_state_file(self.temp_path)
        self.assertTrue(any("missing required key: goal" in error for error in errors))

    def test_05_legal_state_transitions_reach_done_only_after_acceptance(self) -> None:
        self.install()
        self.move_to_verifying()
        state = core.transition_state(
            self.temp_path,
            "DONE",
            reason="all mandatory acceptance passed",
            acceptance_updates=self.mark_all_acceptance(),
        )
        self.assertEqual(state["status"], "DONE")
        self.assertFalse(state["automation_enabled"])
        self.assertEqual(state["stop_reason"], "acceptance_passed")
        self.assertEqual(state["pending_tasks"], [])
        self.assertEqual(state["current_task"], "")
        self.assertEqual(state["current_milestone"], "completed")

    def test_06_illegal_state_transition_is_rejected(self) -> None:
        self.install()
        core.transition_state(self.temp_path, "INSPECTING", reason="inspect")
        core.transition_state(self.temp_path, "PLANNING", reason="plan")
        with self.assertRaises(core.InvalidTransitionError):
            core.transition_state(
                self.temp_path,
                "DONE",
                reason="invalid shortcut",
                acceptance_updates=self.mark_all_acceptance(),
            )

    def test_07_same_strategy_third_failure_enters_replanning(self) -> None:
        self.install()
        self.move_to_executing()
        for _ in range(3):
            state = core.record_failure(
                self.temp_path,
                category="测试错误",
                strategy="route-a",
                error="assertion failed at synthetic line 42",
                root_cause_hypothesis="the same route has a deterministic defect",
                experiment="run the smallest focused test",
                repair="change only the failing branch",
            )
        self.assertEqual(state["status"], "REPLANNING")
        self.assertIn("route-a", state["failed_strategies"])

    def test_08_missing_source_url_is_rejected(self) -> None:
        self.install()
        with self.assertRaises(core.SourceValidationError):
            core.record_research_applied(self.temp_path, source_entry(""), "Do not adopt unsupported claim")

    def test_09_stale_source_detection(self) -> None:
        self.install()
        registry_path = self.temp_path / ".agent" / "SOURCE_REGISTRY.json"
        registry = core.read_json(registry_path)
        registry["sources"][0]["retrieved_at"] = "2020-01-01T00:00:00+00:00"
        core.atomic_write_json(registry_path, registry)
        result = core.check_source_freshness(self.temp_path, max_age_days=30)
        self.assertFalse(result["ok"])
        self.assertGreaterEqual(len(result["stale"]), 1)

    def test_10_lock_conflict_prevents_second_writer(self) -> None:
        self.install()
        first = core.acquire_lock(self.temp_path, owner="writer-a", operation="test", ttl_minutes=5)
        with self.assertRaises(core.LockConflictError):
            core.acquire_lock(self.temp_path, owner="writer-b", operation="test", ttl_minutes=5)
        released = core.release_lock(self.temp_path, run_id=first["run_id"])
        self.assertTrue(released["released"])

    def test_11_expired_lock_recovery_checks_process(self) -> None:
        self.install()
        old = datetime.now(timezone.utc) - timedelta(hours=2)
        payload = {
            "owner": "dead-run",
            "run_id": "expired-run",
            "started_at": (old - timedelta(minutes=30)).isoformat(timespec="seconds"),
            "expires_at": old.isoformat(timespec="seconds"),
            "operation": "test",
            "owner_pid": 99999999,
        }
        core.atomic_write_json(self.temp_path / ".agent" / "LOCK.json", payload)
        result = core.recover_expired_lock(self.temp_path)
        self.assertTrue(result["recovered"])
        self.assertFalse(core.lock_status(self.temp_path).valid)

    def test_12_interruption_resumes_from_next_action(self) -> None:
        self.install()
        state_path = self.temp_path / ".agent" / "TASK_STATE.json"
        state = core.read_json(state_path)
        state["next_action"] = "Run the focused parser acceptance test."
        core.atomic_write_json(state_path, state)
        self.assertEqual(core.select_next_action(self.temp_path), "Run the focused parser acceptance test.")

    def test_13_done_stops_all_modification(self) -> None:
        self.install()
        self.move_to_verifying()
        core.transition_state(
            self.temp_path,
            "DONE",
            reason="accepted",
            acceptance_updates=self.mark_all_acceptance(),
        )
        before = tree_fingerprint(self.temp_path)
        result = core.run_once(self.temp_path)
        after = tree_fingerprint(self.temp_path)
        self.assertFalse(result["modified"])
        self.assertEqual(before, after)

    def test_14_blocked_stops_meaningless_retry_and_report_churn(self) -> None:
        self.install()
        core.transition_state(
            self.temp_path,
            "BLOCKED",
            reason="external account authorization is required",
            next_action="Check whether the approved authorization now exists.",
        )
        before = tree_fingerprint(self.temp_path)
        result = core.run_once(self.temp_path)
        after = tree_fingerprint(self.temp_path)
        self.assertFalse(result["modified"])
        self.assertEqual(before, after)
        self.assertIn("BLOCKED_CHECK_ONLY", result["action"])

    def test_15_automation_prompt_completeness(self) -> None:
        policy = (ROOT / "config" / "schedule-policy.yaml").read_text(encoding="utf-8")
        required = (
            "Autonomous Project Continuation",
            "every 2 hours",
            "Daily Autonomous Project Audit",
            "daily at 08:30",
            "Australia/Sydney",
            "$autonomous-completion-loop",
            ".agent/LOCK.json",
            "RESEARCH_NEEDED",
            "DONE",
            "BLOCKED",
            "禁止 Commit、Push、Merge、Release、Deploy",
        )
        for text in required:
            self.assertIn(text, policy)

    def test_16_uninstall_preserves_user_files_and_state_by_default(self) -> None:
        original = "# User Rules\n\nNever remove this.\n"
        user_file = self.temp_path / "src" / "app.py"
        user_file.parent.mkdir()
        user_file.write_text("print('business code')\n", encoding="utf-8")
        (self.temp_path / "AGENTS.md").write_text(original, encoding="utf-8")
        self.install()
        result = core.uninstall(self.temp_path)
        self.assertTrue(user_file.exists())
        self.assertEqual((self.temp_path / "AGENTS.md").read_text(encoding="utf-8").strip(), original.strip())
        self.assertTrue((self.temp_path / ".agent" / "TASK_STATE.json").exists())
        self.assertFalse((self.temp_path / ".agents" / "skills" / "autonomous-completion-loop").exists())
        self.assertTrue(result["user_files_preserved"])

    def test_17_existing_managed_agents_block_updates_without_duplicate(self) -> None:
        self.install()
        first = core.update_managed_agents_block(self.temp_path / "AGENTS.md")
        second = core.update_managed_agents_block(self.temp_path / "AGENTS.md")
        agents = (self.temp_path / "AGENTS.md").read_text(encoding="utf-8")
        self.assertEqual(agents.count(core.MANAGED_START), 1)
        self.assertEqual(first["managed_block_count"], 1)
        self.assertEqual(second["managed_block_count"], 1)

    def test_18_project_inspection_does_not_read_secrets(self) -> None:
        sentinel = "TOP-SECRET-SENTINEL-MUST-NOT-APPEAR"
        (self.temp_path / ".env").write_text(f"API_KEY={sentinel}\n", encoding="utf-8")
        self.install()
        report = core.inspect_project(self.temp_path)
        serialized = json.dumps(report, ensure_ascii=False)
        self.assertNotIn(sentinel, serialized)
        self.assertFalse(report["security"]["secret_file_contents_read"])
        env_item = next(item for item in report["top_level"] if item["name"] == ".env")
        self.assertTrue(env_item["secret_like_name"])
        self.assertFalse(env_item["content_read"])

    def test_19_runtime_contains_no_forbidden_executable_commands(self) -> None:
        paths = list((ROOT / "acl_loop").rglob("*.py"))
        paths += list((ROOT / "scripts").rglob("*.py"))
        paths += list((ROOT / "skill" / "autonomous-completion-loop" / "scripts").rglob("*.py"))
        findings = core.find_forbidden_command_text(paths)
        self.assertEqual(findings, [])

    def test_20_three_distinct_failed_strategies_enter_blocked(self) -> None:
        self.install()
        self.move_to_executing()
        for strategy in ("route-a", "route-b", "route-c"):
            for _ in range(3):
                state = core.record_failure(
                    self.temp_path,
                    category="架构错误",
                    strategy=strategy,
                    error=f"same deterministic failure for {strategy}",
                    root_cause_hypothesis="the route cannot satisfy the contract",
                    experiment="run a minimal contract probe",
                    repair="attempt the smallest route-specific correction",
                )
        self.assertEqual(state["status"], "BLOCKED")
        self.assertEqual(len(state["failed_strategies"]), 3)
        self.assertIn("three distinct", state["stop_reason"])

    def test_21_full_failure_repair_done_end_to_end_demo(self) -> None:
        self.install()
        core.transition_state(self.temp_path, "INSPECTING", reason="inspect")
        core.transition_state(self.temp_path, "PLANNING", reason="plan")
        core.transition_state(self.temp_path, "EXECUTING", reason="execute")
        core.transition_state(self.temp_path, "VERIFYING", reason="first verification")
        failed = core.record_failure(
            self.temp_path,
            category="测试错误",
            strategy="initial-route",
            error="simulated focused acceptance failure",
            root_cause_hypothesis="one bounded condition is wrong",
            experiment="isolate the bounded condition",
            repair="correct the bounded condition",
        )
        self.assertEqual(failed["status"], "REPAIRING")
        core.transition_state(self.temp_path, "VERIFYING", reason="verification after minimum repair")
        done = core.transition_state(
            self.temp_path,
            "DONE",
            reason="all checks passed after repair",
            acceptance_updates=self.mark_all_acceptance(),
        )
        self.assertEqual(done["status"], "DONE")
        progress = (self.temp_path / ".agent" / "PROGRESS.md").read_text(encoding="utf-8")
        for state in ("INSPECTING", "PLANNING", "EXECUTING", "VERIFYING", "REPAIRING", "DONE"):
            self.assertIn(state, progress if state != "REPAIRING" else (self.temp_path / ".agent" / "FAILURE_LOG.md").read_text(encoding="utf-8"))

    def test_22_research_needed_to_applied_and_execution_demo(self) -> None:
        self.install()
        core.transition_state(self.temp_path, "INSPECTING", reason="inspect")
        core.transition_state(self.temp_path, "RESEARCH_NEEDED", reason="API version uncertain")
        core.transition_state(self.temp_path, "RESEARCHING", reason="official source identified")
        core.transition_state(self.temp_path, "FACT_CHECKING", reason="local minimum validation")
        core.record_research_applied(self.temp_path, source_entry(), "Use the locally validated format")
        state = core.transition_state(self.temp_path, "EXECUTING", reason="research applied to bounded action")
        self.assertEqual(state["status"], "EXECUTING")
        self.assertIn("RESEARCH_APPLIED", (self.temp_path / ".agent" / "RESEARCH_LOG.md").read_text(encoding="utf-8"))
        self.assertIn("https://example.com/official", (self.temp_path / ".agent" / "DECISION_LOG.md").read_text(encoding="utf-8"))

    def test_23_global_skill_installation_to_disposable_root(self) -> None:
        destination_root = self.temp_path / "user-skills"
        result = core.install_global_skill(destination_root)
        skill = destination_root / "autonomous-completion-loop" / "SKILL.md"
        self.assertTrue(skill.exists())
        self.assertEqual(Path(result["skill_file"]).resolve(), skill.resolve())
        text = skill.read_text(encoding="utf-8")
        self.assertIn("name: autonomous-completion-loop", text)
        self.assertIn("description:", text)

    def test_24_installation_does_not_change_business_code(self) -> None:
        business = self.temp_path / "src" / "domain.py"
        business.parent.mkdir()
        business.write_text("VALUE = 7\n", encoding="utf-8")
        before = file_hash(business)
        self.install()
        after = file_hash(business)
        self.assertEqual(before, after)

    def test_25_required_project_files_and_valid_json_schemas_exist(self) -> None:
        required = [
            "README.md",
            "AGENTS.md",
            "LICENSE",
            "CHANGELOG.md",
            "pyproject.toml",
            "config/default-policy.yaml",
            "config/research-policy.yaml",
            "config/safety-policy.yaml",
            "config/schedule-policy.yaml",
            "schemas/task-state.schema.json",
            "schemas/source-registry.schema.json",
            "schemas/acceptance.schema.json",
            "schemas/project-registry.schema.json",
            "skill/autonomous-completion-loop/SKILL.md",
            "docs/AUTOMATION_SETUP.md",
            "docs/OFFICIAL_FORMAT_RESEARCH.md",
        ]
        for relative in required:
            self.assertTrue((ROOT / relative).exists(), relative)
        for path in (ROOT / "schemas").glob("*.json"):
            json.loads(path.read_text(encoding="utf-8"))
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn(".env", gitignore)
        self.assertIn(".env.*", gitignore)
        self.assertIn("!.env.example", gitignore)

    def test_26_github_actions_ci_matrix_contract(self) -> None:
        workflow_path = ROOT / ".github" / "workflows" / "ci.yml"
        self.assertTrue(workflow_path.exists())
        workflow = workflow_path.read_text(encoding="utf-8")
        required = (
            'python-version: ["3.11", "3.12", "3.13"]',
            "fail-fast: false",
            "permissions:",
            "contents: read",
            "persist-credentials: false",
            "python3 -m compileall acl_loop scripts tests",
            "python3 scripts/run_test_suite.py",
            "id: compile",
            "id: suite",
            "id: summary",
            "if: ${{ always() && !cancelled() && (steps.compile.outcome == 'success' || steps.compile.outcome == 'failure') }}",
            "if: ${{ always() && !cancelled() }}",
            "EVIDENCELOOP_COMPILE_OUTCOME: ${{ steps.compile.outcome }}",
            "EVIDENCELOOP_SUITE_OUTCOME: ${{ steps.suite.outcome }}",
            "GITHUB_STEP_SUMMARY",
            "tests/results/ci-matrix-summary.json",
            "tests/results/ci-matrix-summary.txt",
            "tests/results/latest.json",
            "tests/results/latest.txt",
            "evidenceloop-python-${{ matrix.python-version }}-evidence",
            "if-no-files-found: error",
            "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
            "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97",
            "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
        )
        for text in required:
            self.assertIn(text, workflow)
        prohibited = (
            "pull_request_target",
            "secrets.",
            "contents: write",
            "pypi",
            "twine",
            "publish",
            "deploy",
            "continue-on-error",
        )
        lowered = workflow.lower()
        for text in prohibited:
            self.assertNotIn(text, lowered)
        self.assertNotRegex(
            workflow,
            r"(?m)^\s+[A-Za-z0-9_-]+:\s*write\s*$",
        )
        self.assertNotIn("write-all", lowered)
        self.assertNotRegex(workflow, r"secrets\s*\[")
        self.assertNotIn("gh release", lowered)

    def test_27_codex_walkthrough_public_contract(self) -> None:
        walkthrough_path = ROOT / "docs" / "CODEX_INTEGRATION.md"
        self.assertTrue(walkthrough_path.exists())
        walkthrough = walkthrough_path.read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        required = (
            "disposable",
            "mktemp -d",
            "v0.1.0",
            "autonomous-completion-loop",
            "$autonomous-completion-loop",
            "install-project",
            "validate-state",
            "TASK_STATE.json",
            "next_action",
            ".agent/LOCK.json",
            "FAILURE_LOG.md",
            "REPAIRING",
            "uninstall",
            "secret",
            'PYTHONPATH="../evidenceloop"',
            "python3 -B -m unittest",
            "pause the active Codex run",
            '"valid": false',
            'LOCK_STATUS_JSON="$lock_status"',
            "Refusing uninstall: pause writers and clear the active lock first.",
            "raise SystemExit(1)",
            "trap release_rollback_lock EXIT",
            '--operation "rollback-uninstall"',
            "rollback_lock_acquired=true",
            "Scheduled Tasks are optional",
            "a ChatGPT web task cannot access the local folder",
            "AUTOMATION_SETUP_REQUIRED",
            "A green CI run proves only",
        )
        for text in required:
            self.assertIn(text, walkthrough)
        self.assertIn("[Codex integration walkthrough](docs/CODEX_INTEGRATION.md)", readme)
        self.assertIn(
            "Codex Skill integration and optional Scheduled Task setup guidance",
            readme,
        )
        self.assertIn("A green CI run proves only", readme)
        self.assertIn("does not prove output quality", readme)
        self.assertNotIn("EVIDENCELOOP_HOME", walkthrough)
        rollback_section = walkthrough.split("## 7. Rollback", 1)[1].split(
            "## 8. Optional Scheduled Tasks",
            1,
        )[0]
        self.assertLess(
            rollback_section.index("raise SystemExit(1)"),
            rollback_section.index("python3 -m acl_loop.cli uninstall"),
        )
        self.assertLess(
            rollback_section.index('lock --project "$DEMO" acquire'),
            rollback_section.index("python3 -m acl_loop.cli uninstall"),
        )
        self.assertLess(
            rollback_section.index("python3 -m acl_loop.cli uninstall"),
            rollback_section.rindex('lock --project "$DEMO" release'),
        )

        for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", walkthrough):
            if target.startswith(("https://", "http://", "#")):
                continue
            relative = target.split("#", 1)[0]
            self.assertTrue((walkthrough_path.parent / relative).exists(), target)

    def test_28_codex_walkthrough_cli_flow(self) -> None:
        cli_environment = os.environ.copy()
        cli_environment["PYTHONNOUSERSITE"] = "1"
        cli_environment["PYTHONDONTWRITEBYTECODE"] = "1"
        cli_environment["PYTHONPATH"] = str(ROOT)

        def run_cli(*arguments: str) -> dict[str, object]:
            completed = subprocess.run(
                [sys.executable, "-m", "acl_loop.cli", *arguments],
                cwd=self.temp_path,
                env=cli_environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            payload = json.loads(completed.stdout)
            self.assertTrue(payload.get("ok"), payload)
            return payload

        tests_dir = self.temp_path / "tests"
        tests_dir.mkdir()
        (self.temp_path / ".gitignore").write_text(
            ".agent/\n.env\n.env.*\n__pycache__/\n",
            encoding="utf-8",
        )
        (self.temp_path / ".env").write_text(
            "SYNTHETIC_DO_NOT_READ_MARKER=walkthrough-test\n",
            encoding="utf-8",
        )
        answer = self.temp_path / "answer.py"
        answer.write_text("def answer() -> int:\n    return 1\n", encoding="utf-8")
        (tests_dir / "test_answer.py").write_text(
            "import unittest\n"
            "from answer import answer\n\n"
            "class AnswerTest(unittest.TestCase):\n"
            "    def test_answer(self) -> None:\n"
            "        self.assertEqual(answer(), 2)\n",
            encoding="utf-8",
        )
        staged = subprocess.run(
            [
                "git",
                "-C",
                str(self.temp_path),
                "add",
                ".gitignore",
                "answer.py",
                "tests/test_answer.py",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(staged.returncode, 0, staged.stderr)
        committed = subprocess.run(
            [
                "git",
                "-C",
                str(self.temp_path),
                "-c",
                "user.name=EvidenceLoop walkthrough",
                "-c",
                "user.email=walkthrough@example.invalid",
                "commit",
                "-m",
                "Create disposable failing fixture",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(committed.returncode, 0, committed.stderr)
        baseline_head = subprocess.run(
            ["git", "-C", str(self.temp_path), "rev-parse", "HEAD"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(baseline_head.returncode, 0, baseline_head.stderr)
        baseline_commit = baseline_head.stdout.strip()

        acceptance_command = [
            sys.executable,
            "-B",
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-v",
        ]
        initial = subprocess.run(
            acceptance_command,
            cwd=self.temp_path,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(initial.returncode, 0)

        install = run_cli(
            "install-project",
            "--project",
            str(self.temp_path),
            "--goal",
            "Repair the disposable failing test and preserve evidence.",
        )
        self.assertFalse(install["business_code_modified"])
        validation = run_cli("validate-state", "--project", str(self.temp_path))
        self.assertEqual(validation["errors"], [])
        skill = (
            self.temp_path
            / ".agents"
            / "skills"
            / "autonomous-completion-loop"
            / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("name: autonomous-completion-loop", skill)

        run_id = "walkthrough-contract-run"
        acquired = run_cli(
            "lock",
            "--project",
            str(self.temp_path),
            "acquire",
            "--owner",
            "walkthrough-contract-test",
            "--operation",
            "failure-repair-flow",
            "--ttl-minutes",
            "10",
            "--run-id",
            run_id,
        )
        self.assertEqual(acquired["run_id"], run_id)
        active_lock = run_cli("lock", "--project", str(self.temp_path), "status")
        self.assertTrue(active_lock["valid"])

        transitions = (
            ("INSPECTING", "Inspect the disposable repository."),
            ("PLANNING", "Select the minimum repair."),
            ("EXECUTING", "Apply the bounded repair."),
            ("VERIFYING", "Run the original acceptance command."),
        )
        for target, reason in transitions:
            run_cli(
                "transition",
                "--project",
                str(self.temp_path),
                "--to",
                target,
                "--reason",
                reason,
            )

        failed = run_cli(
            "record-failure",
            "--project",
            str(self.temp_path),
            "--category",
            "测试错误",
            "--strategy",
            "disposable-answer-repair-v1",
            "--error",
            "Synthetic assertion expected 2 but received 1.",
            "--root-cause-hypothesis",
            "The disposable answer fixture returns the intentionally wrong value.",
            "--experiment",
            "Change only the fixture return value and rerun the same unittest command.",
            "--repair",
            "Return 2 from answer().",
        )
        self.assertEqual(failed["status"], "REPAIRING")

        answer.write_text(
            "def answer() -> int:\n    return 2  # repaired fixture\n",
            encoding="utf-8",
        )
        repaired = subprocess.run(
            acceptance_command,
            cwd=self.temp_path,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(repaired.returncode, 0, repaired.stderr)

        run_cli(
            "transition",
            "--project",
            str(self.temp_path),
            "--to",
            "VERIFYING",
            "--reason",
            "The minimum repair passed the original acceptance command.",
        )
        validation_before_done = run_cli(
            "validate-state",
            "--project",
            str(self.temp_path),
        )
        inspection = run_cli("inspect", "--project", str(self.temp_path))
        agents = (self.temp_path / "AGENTS.md").read_text(encoding="utf-8")
        failure_log = (
            self.temp_path / ".agent" / "FAILURE_LOG.md"
        ).read_text(encoding="utf-8")
        progress = (
            self.temp_path / ".agent" / "PROGRESS.md"
        ).read_text(encoding="utf-8")
        post_repair_head = subprocess.run(
            ["git", "-C", str(self.temp_path), "rev-parse", "HEAD"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(post_repair_head.returncode, 0, post_repair_head.stderr)
        remotes = subprocess.run(
            ["git", "-C", str(self.temp_path), "remote"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(remotes.returncode, 0, remotes.stderr)
        top_level = {
            item["name"]: item
            for item in inspection["top_level"]
            if isinstance(item, dict) and "name" in item
        }
        inspection_text = json.dumps(inspection, ensure_ascii=False)
        self.assertNotIn("walkthrough-test", inspection_text)
        command_evidence = (
            self.temp_path
            / ".agent"
            / "EVIDENCE"
            / "walkthrough-command-evidence.json"
        )
        core.atomic_write_json(
            command_evidence,
            {
                "schema_version": "1.0",
                "acceptance_command": acceptance_command,
                "initial": {
                    "exit_code": initial.returncode,
                    "stdout": initial.stdout,
                    "stderr": initial.stderr,
                },
                "repaired": {
                    "exit_code": repaired.returncode,
                    "stdout": repaired.stdout,
                    "stderr": repaired.stderr,
                },
                "secret_file_contents_read": inspection["security"][
                    "secret_file_contents_read"
                ],
                "lock_run_id": run_id,
            },
        )
        saved_command_evidence = json.loads(
            command_evidence.read_text(encoding="utf-8")
        )
        self.assertNotEqual(saved_command_evidence["initial"]["exit_code"], 0)
        self.assertEqual(saved_command_evidence["repaired"]["exit_code"], 0)
        acceptance_checks = {
            "state_schema_valid": validation_before_done["errors"] == [],
            "project_skill_installed": (
                self.temp_path
                / ".agents"
                / "skills"
                / "autonomous-completion-loop"
                / "SKILL.md"
            ).exists(),
            "managed_agents_block_valid": (
                agents.count(core.MANAGED_START) == 1
                and agents.count(core.MANAGED_END) == 1
            ),
            "security_boundaries_verified": (
                inspection["security"]["secret_file_contents_read"] is False
                and top_level[".env"]["content_read"] is False
                and "walkthrough-test" not in inspection_text
                and post_repair_head.stdout.strip() == baseline_commit
                and remotes.stdout.strip() == ""
            ),
            "relevant_tests_passed": repaired.returncode == 0,
            "evidence_complete": (
                command_evidence.exists()
                and "disposable-answer-repair-v1" in failure_log
                and "VERIFYING" in progress
            ),
        }
        self.assertEqual(
            set(acceptance_checks),
            set(core.MANDATORY_ACCEPTANCE),
        )
        done_arguments = [
            "transition",
            "--project",
            str(self.temp_path),
            "--to",
            "DONE",
            "--reason",
            "Every synthetic walkthrough acceptance check passed.",
        ]
        for name in sorted(acceptance_checks):
            self.assertTrue(acceptance_checks[name], name)
            if acceptance_checks[name]:
                done_arguments.extend(["--accept", name])
        done = run_cli(*done_arguments)
        self.assertEqual(done["status"], "DONE")

        released = run_cli(
            "lock",
            "--project",
            str(self.temp_path),
            "release",
            "--run-id",
            run_id,
        )
        self.assertTrue(released["released"])
        final_fingerprint = tree_fingerprint(self.temp_path)
        final_validation = run_cli("validate-state", "--project", str(self.temp_path))
        self.assertEqual(final_validation["errors"], [])
        acceptance = run_cli("acceptance", "--project", str(self.temp_path))
        self.assertTrue(acceptance["passed"])
        next_action = run_cli("next-action", "--project", str(self.temp_path))
        self.assertIn("READ_ONLY", str(next_action["next_action"]))
        final_lock = run_cli("lock", "--project", str(self.temp_path), "status")
        self.assertFalse(final_lock["valid"])
        final_test = subprocess.run(
            acceptance_command,
            cwd=self.temp_path,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(final_test.returncode, 0, final_test.stderr)
        self.assertEqual(tree_fingerprint(self.temp_path), final_fingerprint)
        self.assertIn("disposable-answer-repair-v1", failure_log)

        rollback_record: dict[str, object]
        with tempfile.TemporaryDirectory(prefix="acl-loop-rollback-test-") as temporary:
            rollback_project = Path(temporary)
            rollback_record = {
                "path": str(rollback_project),
                "created": True,
                "cleaned": False,
            }
            rollback_git = subprocess.run(
                ["git", "init", "-q", str(rollback_project)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(rollback_git.returncode, 0, rollback_git.stderr)
            user_file = rollback_project / "user.txt"
            user_file.write_text("preserve me\n", encoding="utf-8")
            run_cli(
                "install-project",
                "--project",
                str(rollback_project),
                "--goal",
                "Validate rollback without removing user files or evidence.",
            )
            rollback_lock = run_cli(
                "lock",
                "--project",
                str(rollback_project),
                "status",
            )
            self.assertFalse(rollback_lock["valid"])
            rollback_run_id = "walkthrough-rollback-run"
            rollback_acquire = run_cli(
                "lock",
                "--project",
                str(rollback_project),
                "acquire",
                "--owner",
                "walkthrough-rollback-test",
                "--operation",
                "rollback-uninstall",
                "--ttl-minutes",
                "10",
                "--run-id",
                rollback_run_id,
            )
            self.assertEqual(rollback_acquire["run_id"], rollback_run_id)
            owned_rollback_lock = run_cli(
                "lock",
                "--project",
                str(rollback_project),
                "status",
            )
            self.assertTrue(owned_rollback_lock["valid"])
            self.assertEqual(
                owned_rollback_lock["data"]["run_id"],
                rollback_run_id,
            )
            uninstall = run_cli(
                "uninstall",
                "--project",
                str(rollback_project),
            )
            self.assertTrue(uninstall["user_files_preserved"])
            rollback_release = run_cli(
                "lock",
                "--project",
                str(rollback_project),
                "release",
                "--run-id",
                rollback_run_id,
            )
            self.assertTrue(rollback_release["released"])
            released_rollback_lock = run_cli(
                "lock",
                "--project",
                str(rollback_project),
                "status",
            )
            self.assertFalse(released_rollback_lock["valid"])
            self.assertEqual(released_rollback_lock["data"]["run_id"], "")
            self.assertTrue(user_file.exists())
            self.assertTrue(
                (rollback_project / ".agent" / "TASK_STATE.json").exists()
            )
            self.assertFalse(
                (
                    rollback_project
                    / ".agents"
                    / "skills"
                    / "autonomous-completion-loop"
                ).exists()
            )
            rollback_agents = rollback_project / "AGENTS.md"
            self.assertNotIn(
                core.MANAGED_START,
                rollback_agents.read_text(encoding="utf-8"),
            )
            rollback_record["verified"] = True
        rollback_record["cleaned"] = not Path(str(rollback_record["path"])).exists()
        self.record["rollback_demo"] = rollback_record


if __name__ == "__main__":
    unittest.main(verbosity=2)
