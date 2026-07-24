from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
