from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent
SOURCE_RESOURCES_AVAILABLE = (
    (PROJECT_ROOT / "pyproject.toml").is_file()
    and (PROJECT_ROOT / "templates").is_dir()
    and (PROJECT_ROOT / "skill" / "autonomous-completion-loop").is_dir()
)
RESOURCE_ROOT = PROJECT_ROOT if SOURCE_RESOURCES_AVAILABLE else PACKAGE_ROOT / "resources"
TEMPLATES_DIR = RESOURCE_ROOT / "templates"
SKILL_SOURCE_DIR = RESOURCE_ROOT / "skill" / "autonomous-completion-loop"
MANAGED_START = "<!-- AUTONOMOUS_COMPLETION_LOOP:START -->"
MANAGED_END = "<!-- AUTONOMOUS_COMPLETION_LOOP:END -->"

ALL_STATES = (
    "INIT",
    "INSPECTING",
    "RESEARCH_NEEDED",
    "RESEARCHING",
    "FACT_CHECKING",
    "PLANNING",
    "EXECUTING",
    "VERIFYING",
    "REPAIRING",
    "REPLANNING",
    "DONE",
    "BLOCKED",
)
TERMINAL_STATES = frozenset({"DONE", "BLOCKED"})
ACTIVE_STATES = frozenset(set(ALL_STATES) - set(TERMINAL_STATES))
MANDATORY_ACCEPTANCE = (
    "state_schema_valid",
    "project_skill_installed",
    "managed_agents_block_valid",
    "security_boundaries_verified",
    "relevant_tests_passed",
    "evidence_complete",
)

ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "INIT": frozenset({"INSPECTING", "BLOCKED"}),
    "INSPECTING": frozenset({"RESEARCH_NEEDED", "PLANNING", "VERIFYING", "BLOCKED"}),
    "RESEARCH_NEEDED": frozenset({"RESEARCHING", "BLOCKED"}),
    "RESEARCHING": frozenset({"FACT_CHECKING", "RESEARCH_NEEDED", "BLOCKED"}),
    "FACT_CHECKING": frozenset({"PLANNING", "RESEARCH_NEEDED", "EXECUTING", "BLOCKED"}),
    "PLANNING": frozenset({"EXECUTING", "RESEARCH_NEEDED", "REPLANNING", "BLOCKED"}),
    "EXECUTING": frozenset({"VERIFYING", "REPAIRING", "RESEARCH_NEEDED", "REPLANNING", "BLOCKED"}),
    "VERIFYING": frozenset({"DONE", "REPAIRING", "REPLANNING", "RESEARCH_NEEDED", "BLOCKED"}),
    "REPAIRING": frozenset({"VERIFYING", "REPLANNING", "RESEARCH_NEEDED", "BLOCKED"}),
    "REPLANNING": frozenset({"PLANNING", "RESEARCH_NEEDED", "BLOCKED"}),
    "DONE": frozenset(),
    "BLOCKED": frozenset({"INSPECTING"}),
}

SECRET_NAME_PATTERNS = (
    re.compile(r"(^|[._-])\.env($|[._-])", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"credential", re.IGNORECASE),
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"private[_-]?key", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
)
ERROR_CATEGORIES = frozenset(
    {
        "代码错误",
        "测试错误",
        "依赖错误",
        "配置错误",
        "环境错误",
        "权限错误",
        "外部服务错误",
        "数据错误",
        "需求冲突",
        "架构错误",
        "第三方兼容错误",
    }
)


class LoopError(RuntimeError):
    """Base error for deterministic completion-loop failures."""


class StateValidationError(LoopError):
    pass


class InvalidTransitionError(LoopError):
    pass


class AcceptanceError(LoopError):
    pass


class SourceValidationError(LoopError):
    pass


class LockConflictError(LoopError):
    pass


@dataclass(frozen=True)
class LockStatus:
    exists: bool
    valid: bool
    expired: bool
    process_alive: bool
    data: dict[str, Any]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_write_json(path: Path, payload: Any) -> None:
    atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n")


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def append_markdown(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    spacer = "" if not existing or existing.endswith("\n\n") else "\n"
    atomic_write_text(path, existing + spacer + content.rstrip() + "\n\n")


def default_task_state(project: str, goal: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "project": project,
        "goal": goal,
        "status": "INIT",
        "current_milestone": "installation",
        "current_task": "inspect real project state",
        "completed_tasks": [],
        "pending_tasks": ["inspect real project state", "verify installation", "run acceptance"],
        "acceptance_results": {name: False for name in MANDATORY_ACCEPTANCE},
        "current_strategy": "inspect-first",
        "failed_strategies": [],
        "retry_count": 0,
        "strategy_count": 0,
        "failure_fingerprints": {},
        "last_error": None,
        "last_progress_at": None,
        "last_research_at": None,
        "next_action": "Inspect Git, files, dependencies, runtime, and existing claims without reading secrets.",
        "automation_enabled": True,
        "stop_reason": None,
        "last_transition_at": utc_now(),
        "run_count": 0,
    }


def _type_error(key: str, expected: str) -> str:
    return f"{key} must be {expected}"


def validate_state(state: dict[str, Any]) -> list[str]:
    required = {
        "schema_version",
        "project",
        "goal",
        "status",
        "current_milestone",
        "current_task",
        "completed_tasks",
        "pending_tasks",
        "acceptance_results",
        "current_strategy",
        "failed_strategies",
        "retry_count",
        "strategy_count",
        "last_error",
        "last_progress_at",
        "last_research_at",
        "next_action",
        "automation_enabled",
        "stop_reason",
    }
    errors = [f"missing required key: {key}" for key in sorted(required - set(state))]
    if state.get("schema_version") != "1.0":
        errors.append("schema_version must equal 1.0")
    if state.get("status") not in ALL_STATES:
        errors.append(f"status must be one of {', '.join(ALL_STATES)}")
    for key in ("project", "goal", "current_milestone", "current_task", "current_strategy", "next_action"):
        if key in state and not isinstance(state[key], str):
            errors.append(_type_error(key, "a string"))
    for key in ("completed_tasks", "pending_tasks", "failed_strategies"):
        if key in state and not isinstance(state[key], list):
            errors.append(_type_error(key, "an array"))
    if "acceptance_results" in state and not isinstance(state["acceptance_results"], dict):
        errors.append(_type_error("acceptance_results", "an object"))
    for key in ("retry_count", "strategy_count"):
        if key in state and (not isinstance(state[key], int) or isinstance(state[key], bool) or state[key] < 0):
            errors.append(f"{key} must be a non-negative integer")
    if "automation_enabled" in state and not isinstance(state["automation_enabled"], bool):
        errors.append(_type_error("automation_enabled", "a boolean"))
    if state.get("status") == "DONE":
        passed, missing = check_acceptance(state)
        if not passed:
            errors.append("DONE requires every mandatory acceptance item to pass: " + ", ".join(missing))
        if state.get("stop_reason") != "acceptance_passed":
            errors.append("DONE requires stop_reason=acceptance_passed")
    if state.get("status") == "BLOCKED" and not state.get("stop_reason"):
        errors.append("BLOCKED requires a concrete stop_reason")
    return errors


def validate_state_file(project_root: Path) -> list[str]:
    path = project_root / ".agent" / "TASK_STATE.json"
    if not path.exists():
        return [f"missing state file: {path}"]
    try:
        state = read_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid JSON: {exc}"]
    if not isinstance(state, dict):
        return ["TASK_STATE.json root must be an object"]
    return validate_state(state)


def check_acceptance(state_or_root: dict[str, Any] | Path) -> tuple[bool, list[str]]:
    if isinstance(state_or_root, Path):
        state = read_json(state_or_root / ".agent" / "TASK_STATE.json")
    else:
        state = state_or_root
    results = state.get("acceptance_results", {})
    missing = [name for name in MANDATORY_ACCEPTANCE if results.get(name) is not True]
    return not missing, missing


def _write_transition_evidence(project_root: Path, old: str, new: str, reason: str) -> None:
    append_markdown(
        project_root / ".agent" / "PROGRESS.md",
        f"## {utc_now()} — State transition\n\n- From: `{old}`\n- To: `{new}`\n- Reason: {reason}",
    )


def transition_state(
    project_root: Path,
    new_status: str,
    *,
    reason: str,
    next_action: str | None = None,
    stop_reason: str | None = None,
    acceptance_updates: dict[str, bool] | None = None,
) -> dict[str, Any]:
    state_path = project_root / ".agent" / "TASK_STATE.json"
    state = read_json(state_path)
    errors = validate_state(state)
    if errors:
        raise StateValidationError("; ".join(errors))
    current = state["status"]
    if new_status not in ALL_STATES:
        raise InvalidTransitionError(f"unknown target state: {new_status}")
    if new_status not in ALLOWED_TRANSITIONS[current]:
        raise InvalidTransitionError(f"transition {current} -> {new_status} is not allowed")
    if acceptance_updates:
        for key, value in acceptance_updates.items():
            if key not in MANDATORY_ACCEPTANCE:
                raise AcceptanceError(f"unknown mandatory acceptance item: {key}")
            if not isinstance(value, bool):
                raise AcceptanceError(f"acceptance value for {key} must be boolean")
            state.setdefault("acceptance_results", {})[key] = value
    if new_status == "DONE":
        passed, missing = check_acceptance(state)
        if not passed:
            raise AcceptanceError("cannot enter DONE; failed acceptance: " + ", ".join(missing))
        completed = [str(item) for item in state.get("completed_tasks", [])]
        for item in [state.get("current_task"), *state.get("pending_tasks", [])]:
            if isinstance(item, str) and item.strip() and item not in completed:
                completed.append(item)
        state["completed_tasks"] = completed
        state["pending_tasks"] = []
        state["current_task"] = ""
        state["current_milestone"] = "completed"
        state["stop_reason"] = "acceptance_passed"
        state["next_action"] = "No further modification. Preserve final evidence and remain read-only."
        state["automation_enabled"] = False
    elif new_status == "BLOCKED":
        concrete_reason = stop_reason or reason
        if not concrete_reason.strip():
            raise InvalidTransitionError("BLOCKED requires a concrete reason")
        state["stop_reason"] = concrete_reason
        state["next_action"] = next_action or "Check only whether the named unblock condition has changed."
    else:
        state["stop_reason"] = None
        if next_action is not None:
            state["next_action"] = next_action
    state["status"] = new_status
    state["last_transition_at"] = utc_now()
    if new_status not in TERMINAL_STATES:
        state["last_progress_at"] = utc_now()
    post_errors = validate_state(state)
    if post_errors:
        raise StateValidationError("; ".join(post_errors))
    atomic_write_json(state_path, state)
    _write_transition_evidence(project_root, current, new_status, reason)
    return state


def _normalise_error(error: str) -> str:
    collapsed = re.sub(r"\s+", " ", error.strip())
    return re.sub(r"\b(?:0x)?[0-9a-f]{8,}\b", "<id>", collapsed, flags=re.IGNORECASE)[:2000]


def record_failure(
    project_root: Path,
    *,
    category: str,
    strategy: str,
    error: str,
    root_cause_hypothesis: str,
    experiment: str,
    repair: str,
) -> dict[str, Any]:
    if category not in ERROR_CATEGORIES:
        raise LoopError(f"unsupported error category: {category}")
    state_path = project_root / ".agent" / "TASK_STATE.json"
    state = read_json(state_path)
    if state["status"] in TERMINAL_STATES:
        raise InvalidTransitionError(f"cannot record retry activity while state is {state['status']}")
    normalized = _normalise_error(error)
    fingerprint = hashlib.sha256(f"{strategy}\0{category}\0{normalized}".encode("utf-8")).hexdigest()[:16]
    counts = state.setdefault("failure_fingerprints", {})
    counts[fingerprint] = int(counts.get(fingerprint, 0)) + 1
    same_strategy_count = counts[fingerprint]
    state["retry_count"] = int(state.get("retry_count", 0)) + 1
    state["last_error"] = {
        "at": utc_now(),
        "category": category,
        "strategy": strategy,
        "fingerprint": fingerprint,
        "message": normalized,
    }
    if same_strategy_count >= 3:
        if strategy not in state["failed_strategies"]:
            state["failed_strategies"].append(strategy)
            state["strategy_count"] = int(state.get("strategy_count", 0)) + 1
        if len(state["failed_strategies"]) >= 3:
            state["status"] = "BLOCKED"
            state["stop_reason"] = "three distinct evidence-backed strategies failed and no self-service route remains"
            state["next_action"] = "Supply or resolve the minimum external condition documented in FAILURE_LOG.md."
        else:
            state["status"] = "REPLANNING"
            state["next_action"] = "Retire the failed strategy and design a materially different route using new evidence."
    elif same_strategy_count == 2:
        state["status"] = "REPAIRING"
        state["next_action"] = "Re-check the root-cause hypothesis with a smaller discriminating experiment."
    else:
        state["status"] = "REPAIRING"
        state["next_action"] = "Apply the minimum repair, then rerun the original acceptance command."
    state["last_progress_at"] = utc_now()
    errors = validate_state(state)
    if errors:
        raise StateValidationError("; ".join(errors))
    atomic_write_json(state_path, state)
    append_markdown(
        project_root / ".agent" / "FAILURE_LOG.md",
        "\n".join(
            [
                f"## {utc_now()} — {category}",
                "",
                f"- Strategy: `{strategy}`",
                f"- Fingerprint: `{fingerprint}`",
                f"- Same failure count: {same_strategy_count}",
                f"- Error: `{normalized}`",
                f"- Root-cause hypothesis: {root_cause_hypothesis}",
                f"- Discriminating experiment: {experiment}",
                f"- Minimum repair: {repair}",
                f"- Resulting state: `{state['status']}`",
            ]
        ),
    )
    return state


def is_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_source_entry(entry: dict[str, Any]) -> list[str]:
    required = {
        "question",
        "claim",
        "source_title",
        "source_url",
        "publisher",
        "source_type",
        "published_at",
        "retrieved_at",
        "applicable_version",
        "evidence_summary",
        "confidence",
        "local_validation",
        "limitations",
    }
    errors = [f"missing source field: {key}" for key in sorted(required - set(entry))]
    if not is_http_url(str(entry.get("source_url", ""))):
        errors.append("source_url must be an absolute http(s) URL")
    if entry.get("confidence") not in {"low", "medium", "high"}:
        errors.append("confidence must be low, medium, or high")
    if entry.get("local_validation") not in {"pending", "passed", "failed"}:
        errors.append("local_validation must be pending, passed, or failed")
    try:
        parse_datetime(str(entry.get("retrieved_at", "")))
    except (ValueError, TypeError):
        errors.append("retrieved_at must be ISO-8601")
    return errors


def validate_source_registry(registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if registry.get("schema_version") != "1.0":
        errors.append("source registry schema_version must equal 1.0")
    sources = registry.get("sources")
    if not isinstance(sources, list):
        return errors + ["sources must be an array"]
    for index, entry in enumerate(sources):
        if not isinstance(entry, dict):
            errors.append(f"sources[{index}] must be an object")
            continue
        errors.extend(f"sources[{index}]: {error}" for error in validate_source_entry(entry))
    return errors


def check_source_freshness(project_root: Path, max_age_days: int = 30) -> dict[str, Any]:
    registry_path = project_root / ".agent" / "SOURCE_REGISTRY.json"
    registry = read_json(registry_path)
    errors = validate_source_registry(registry)
    if errors:
        raise SourceValidationError("; ".join(errors))
    now = datetime.now(timezone.utc)
    stale: list[dict[str, Any]] = []
    for entry in registry["sources"]:
        retrieved = parse_datetime(entry["retrieved_at"])
        assert retrieved is not None
        age = now - retrieved
        if age > timedelta(days=max_age_days):
            stale.append(
                {
                    "source_url": entry["source_url"],
                    "retrieved_at": entry["retrieved_at"],
                    "age_days": age.days,
                }
            )
    return {"ok": not stale, "max_age_days": max_age_days, "stale": stale, "checked_at": utc_now()}


def record_research_applied(project_root: Path, entry: dict[str, Any], decision: str) -> None:
    errors = validate_source_entry(entry)
    if errors:
        raise SourceValidationError("; ".join(errors))
    registry_path = project_root / ".agent" / "SOURCE_REGISTRY.json"
    registry = read_json(registry_path) if registry_path.exists() else {"schema_version": "1.0", "sources": []}
    registry.setdefault("sources", []).append(entry)
    registry_errors = validate_source_registry(registry)
    if registry_errors:
        raise SourceValidationError("; ".join(registry_errors))
    atomic_write_json(registry_path, registry)
    event = (
        f"## {utc_now()} — RESEARCH_APPLIED\n\n"
        f"- Claim: {entry['claim']}\n"
        f"- Source: {entry['source_title']} — {entry['source_url']}\n"
        f"- Applicable version: {entry['applicable_version']}\n"
        f"- Local validation: {entry['local_validation']}\n"
        f"- Decision: {decision}"
    )
    append_markdown(project_root / ".agent" / "RESEARCH_LOG.md", event)
    append_markdown(project_root / ".agent" / "DECISION_LOG.md", event)
    state_path = project_root / ".agent" / "TASK_STATE.json"
    if state_path.exists():
        state = read_json(state_path)
        state["last_research_at"] = utc_now()
        atomic_write_json(state_path, state)


def _pid_alive(pid: int | None) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def lock_status(project_root: Path) -> LockStatus:
    path = project_root / ".agent" / "LOCK.json"
    if not path.exists():
        return LockStatus(False, False, False, False, {})
    try:
        data = read_json(path)
    except (OSError, json.JSONDecodeError):
        return LockStatus(True, False, False, False, {})
    if not data.get("run_id"):
        return LockStatus(True, False, False, False, data)
    expires = parse_datetime(data.get("expires_at"))
    expired = expires is not None and expires <= datetime.now(timezone.utc)
    alive = _pid_alive(data.get("owner_pid"))
    valid = not expired and bool(data.get("owner")) and bool(data.get("operation"))
    return LockStatus(True, valid, expired, alive, data)


def acquire_lock(
    project_root: Path,
    *,
    owner: str,
    operation: str,
    ttl_minutes: int = 30,
    run_id: str | None = None,
) -> dict[str, Any]:
    status = lock_status(project_root)
    if status.valid:
        raise LockConflictError(
            f"active lock owned by {status.data.get('owner')} run_id={status.data.get('run_id')}"
        )
    if status.exists and status.data.get("run_id") and (not status.expired or status.process_alive):
        raise LockConflictError("lock cannot be recovered because it is unexpired or its process is alive")
    now = datetime.now(timezone.utc)
    payload = {
        "owner": owner,
        "run_id": run_id or str(uuid.uuid4()),
        "started_at": now.isoformat(timespec="seconds"),
        "expires_at": (now + timedelta(minutes=ttl_minutes)).isoformat(timespec="seconds"),
        "operation": operation,
        "owner_pid": os.getpid(),
    }
    atomic_write_json(project_root / ".agent" / "LOCK.json", payload)
    return payload


def release_lock(project_root: Path, *, run_id: str, force_expired: bool = False) -> dict[str, Any]:
    status = lock_status(project_root)
    if not status.exists or not status.data.get("run_id"):
        return {"released": False, "reason": "no active lock"}
    if status.data.get("run_id") != run_id:
        if not (force_expired and status.expired and not status.process_alive):
            raise LockConflictError("run_id does not own the lock")
    empty = {
        "owner": "",
        "run_id": "",
        "started_at": "",
        "expires_at": "",
        "operation": "",
        "owner_pid": None,
    }
    atomic_write_json(project_root / ".agent" / "LOCK.json", empty)
    return {"released": True, "run_id": run_id}


def recover_expired_lock(project_root: Path) -> dict[str, Any]:
    status = lock_status(project_root)
    if not status.exists or not status.data.get("run_id"):
        return {"recovered": False, "reason": "no active lock"}
    if not status.expired:
        raise LockConflictError("lock is not expired")
    if status.process_alive:
        raise LockConflictError("expired timestamp exists but owner process is still alive")
    old = status.data.copy()
    result = release_lock(project_root, run_id=str(old["run_id"]), force_expired=True)
    append_markdown(
        project_root / ".agent" / "AUTOMATION_REPORT.md",
        f"## {utc_now()} — Expired lock recovered\n\n- Previous owner: `{old.get('owner')}`\n- Previous run: `{old.get('run_id')}`\n- Operation: `{old.get('operation')}`",
    )
    return {"recovered": True, "previous": old, **result}


def _run_git(project_root: Path, args: list[str]) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            ["git", "-C", str(project_root), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"exit_code": None, "stdout": "", "stderr": str(exc)}
    return {
        "exit_code": completed.returncode,
        "stdout": completed.stdout.rstrip(),
        "stderr": completed.stderr.rstrip(),
    }


def _is_secret_name(name: str) -> bool:
    return any(pattern.search(name) for pattern in SECRET_NAME_PATTERNS)


def inspect_project(project_root: Path) -> dict[str, Any]:
    root = project_root.expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise LoopError(f"project directory does not exist: {root}")
    top_level: list[dict[str, Any]] = []
    for path in sorted(root.iterdir(), key=lambda item: item.name.casefold()):
        if path.name == ".git":
            top_level.append({"name": path.name, "kind": "directory", "content_read": False})
            continue
        secret = _is_secret_name(path.name)
        item = {
            "name": path.name,
            "kind": "directory" if path.is_dir() else "file",
            "content_read": False,
            "secret_like_name": secret,
        }
        if path.is_file():
            try:
                item["size_bytes"] = path.stat().st_size
            except OSError:
                item["size_bytes"] = None
        top_level.append(item)
    markers = {}
    for name in ("AGENTS.md", "README.md", "package.json", "pyproject.toml", "Cargo.toml", "go.mod", "requirements.txt"):
        candidate = root / name
        markers[name] = candidate.exists()
    git_inside = _run_git(root, ["rev-parse", "--is-inside-work-tree"])
    report = {
        "schema_version": "1.0",
        "inspected_at": utc_now(),
        "project_root": str(root),
        "is_git_repository": git_inside["exit_code"] == 0 and git_inside["stdout"] == "true",
        "git_status": _run_git(root, ["status", "--short", "--branch"]),
        "git_head": _run_git(root, ["rev-parse", "HEAD"]),
        "markers": markers,
        "top_level": top_level,
        "security": {
            "secret_file_contents_read": False,
            "inspection_policy": "metadata and Git evidence only",
        },
    }
    evidence_dir = root / ".agent" / "EVIDENCE"
    if evidence_dir.exists():
        atomic_write_json(evidence_dir / "latest-project-inspection.json", report)
    return report


def _managed_block() -> str:
    return f"""{MANAGED_START}
## EvidenceLoop

For requests such as continuous execution, automatic correction, resume from progress, external verification, or complete-before-reporting, invoke `$autonomous-completion-loop` and treat `.agent/TASK_STATE.json` as the resumable state authority.

Required cycle:

```text
read state → inspect real state → acquire lock → choose smallest verifiable action
→ research official sources when needed → execute → verify → save evidence
→ update next_action → release lock
```

Rules:

- Never trust an unsupported historical completion claim.
- Never enter `DONE` except through `VERIFYING` after mandatory acceptance passes.
- Stop modifying after `DONE`.
- At `BLOCKED`, check only the named unblock condition and do not repeat unchanged reports.
- Do not read secrets or perform commit, push, merge, release, deployment, paid, destructive, or irreversible actions.
{MANAGED_END}"""


def update_managed_agents_block(path: Path) -> dict[str, Any]:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    block = _managed_block()
    pattern = re.compile(re.escape(MANAGED_START) + r".*?" + re.escape(MANAGED_END), re.DOTALL)
    matches = list(pattern.finditer(existing))
    if len(matches) > 1:
        raise LoopError("multiple managed blocks found; refusing ambiguous rewrite")
    if matches:
        updated = pattern.sub(block, existing, count=1)
        action = "updated"
    else:
        separator = "" if not existing else ("\n" if existing.endswith("\n") else "\n\n")
        updated = existing + separator + block + "\n"
        action = "appended" if existing else "created"
    if updated != existing:
        atomic_write_text(path, updated)
    return {"action": action, "managed_block_count": len(pattern.findall(updated))}


def _copy_tree(source: Path, destination: Path) -> None:
    if not source.exists():
        raise LoopError(f"missing install source: {source}")
    shutil.copytree(source, destination, dirs_exist_ok=True)


def install_global_skill(destination_root: Path | None = None) -> dict[str, Any]:
    root = (destination_root or (Path.home() / ".agents" / "skills")).expanduser().resolve()
    destination = root / "autonomous-completion-loop"
    _copy_tree(SKILL_SOURCE_DIR, destination)
    skill_file = destination / "SKILL.md"
    if not skill_file.exists():
        raise LoopError("global Skill installation did not produce SKILL.md")
    return {"installed": True, "destination": str(destination), "skill_file": str(skill_file)}


def _template_content(name: str) -> str:
    path = TEMPLATES_DIR / name
    if not path.exists():
        raise LoopError(f"missing template: {path}")
    return path.read_text(encoding="utf-8")


def _create_initial_state(project_root: Path, goal: str) -> None:
    state_path = project_root / ".agent" / "TASK_STATE.json"
    if not state_path.exists():
        atomic_write_json(state_path, default_task_state(project_root.name, goal))


def install_project(project_root: Path, *, goal: str) -> dict[str, Any]:
    root = project_root.expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise LoopError(f"project directory does not exist: {root}")
    agent_dir = root / ".agent"
    evidence_dir = agent_dir / "EVIDENCE"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rollback_dir = evidence_dir / f"rollback-before-install-{timestamp}"
    agents_path = root / "AGENTS.md"
    if agents_path.exists():
        rollback_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(agents_path, rollback_dir / "AGENTS.md")
    _create_initial_state(root, goal)
    template_names = (
        "TASK_PLAN.md",
        "PROGRESS.md",
        "FAILURE_LOG.md",
        "RESEARCH_LOG.md",
        "SOURCE_REGISTRY.json",
        "DECISION_LOG.md",
        "ACCEPTANCE.md",
        "AUTOMATION_REPORT.md",
        "LOCK.json",
        "FINAL_HANDOFF.md",
    )
    created: list[str] = []
    preserved: list[str] = []
    for name in template_names:
        destination = agent_dir / name
        if destination.exists():
            preserved.append(str(destination.relative_to(root)))
            continue
        atomic_write_text(destination, _template_content(name))
        created.append(str(destination.relative_to(root)))
    skill_destination = root / ".agents" / "skills" / "autonomous-completion-loop"
    _copy_tree(SKILL_SOURCE_DIR, skill_destination)
    managed = update_managed_agents_block(agents_path)
    inspection = inspect_project(root)
    result = {
        "installed_at": utc_now(),
        "project_root": str(root),
        "goal": goal,
        "created": created,
        "preserved": preserved,
        "project_skill": str(skill_destination),
        "agents": managed,
        "rollback_dir": str(rollback_dir) if rollback_dir.exists() else None,
        "inspection": inspection,
        "business_code_modified": False,
    }
    atomic_write_json(evidence_dir / "installation-result.json", result)
    return result


def uninstall(
    project_root: Path,
    *,
    remove_project_skill: bool = True,
    remove_managed_block: bool = True,
    remove_state: bool = False,
    global_skill_root: Path | None = None,
    remove_global_skill: bool = False,
) -> dict[str, Any]:
    root = project_root.expanduser().resolve()
    changes: list[str] = []
    if remove_managed_block:
        agents_path = root / "AGENTS.md"
        if agents_path.exists():
            existing = agents_path.read_text(encoding="utf-8")
            pattern = re.compile(
                r"\n?" + re.escape(MANAGED_START) + r".*?" + re.escape(MANAGED_END) + r"\n?",
                re.DOTALL,
            )
            updated, count = pattern.subn("\n", existing, count=1)
            if count:
                atomic_write_text(agents_path, updated.lstrip("\n") if not updated.strip() else updated)
                changes.append("removed managed AGENTS block")
    if remove_project_skill:
        skill = root / ".agents" / "skills" / "autonomous-completion-loop"
        if skill.exists():
            shutil.rmtree(skill)
            changes.append("removed project Skill")
    if remove_state:
        state_dir = root / ".agent"
        if state_dir.exists():
            shutil.rmtree(state_dir)
            changes.append("removed .agent state directory")
    if remove_global_skill:
        base = (global_skill_root or (Path.home() / ".agents" / "skills")).expanduser().resolve()
        skill = base / "autonomous-completion-loop"
        if skill.exists():
            shutil.rmtree(skill)
            changes.append("removed global Skill")
    return {"project_root": str(root), "changes": changes, "user_files_preserved": not remove_state}


def select_next_action(state_or_root: dict[str, Any] | Path) -> str:
    state = read_json(state_or_root / ".agent" / "TASK_STATE.json") if isinstance(state_or_root, Path) else state_or_root
    status = state["status"]
    if status == "DONE":
        return "READ_ONLY: verify final evidence only; do not modify the project."
    if status == "BLOCKED":
        return f"BLOCKED_CHECK_ONLY: {state.get('next_action') or state.get('stop_reason')}"
    explicit = str(state.get("next_action", "")).strip()
    if explicit:
        return explicit
    defaults = {
        "INIT": "Inspect real project state.",
        "INSPECTING": "Reconcile claims with filesystem, Git, dependencies, and tests.",
        "RESEARCH_NEEDED": "Formulate the exact unknown and retrieve an official source with URL and version.",
        "RESEARCHING": "Collect the minimum authoritative evidence.",
        "FACT_CHECKING": "Validate the adopted external claim locally.",
        "PLANNING": "Choose the smallest verifiable action with rollback and acceptance.",
        "EXECUTING": "Execute one reversible action.",
        "VERIFYING": "Run the original acceptance command and store evidence.",
        "REPAIRING": "Test the root-cause hypothesis and apply the minimum fix.",
        "REPLANNING": "Choose a materially different strategy supported by new evidence.",
    }
    return defaults[status]


def detect_stalled_task(project_root: Path, threshold_hours: int = 4) -> dict[str, Any]:
    state = read_json(project_root / ".agent" / "TASK_STATE.json")
    if state["status"] in TERMINAL_STATES:
        return {"stalled": False, "reason": f"terminal state {state['status']}"}
    last = parse_datetime(state.get("last_progress_at") or state.get("last_transition_at"))
    if last is None:
        return {"stalled": True, "reason": "no progress timestamp", "threshold_hours": threshold_hours}
    elapsed = datetime.now(timezone.utc) - last
    return {
        "stalled": elapsed > timedelta(hours=threshold_hours),
        "elapsed_seconds": int(elapsed.total_seconds()),
        "threshold_hours": threshold_hours,
        "last_progress_at": last.isoformat(timespec="seconds"),
    }


def generate_status_report(project_root: Path) -> dict[str, Any]:
    state_path = project_root / ".agent" / "TASK_STATE.json"
    state = read_json(state_path)
    validation_errors = validate_state(state)
    acceptance_ok, missing = check_acceptance(state)
    inspection = inspect_project(project_root)
    lock = lock_status(project_root)
    report = {
        "generated_at": utc_now(),
        "project_root": str(project_root.resolve()),
        "state": state,
        "state_valid": not validation_errors,
        "state_errors": validation_errors,
        "acceptance_passed": acceptance_ok,
        "acceptance_missing": missing,
        "next_action": select_next_action(state),
        "stalled": detect_stalled_task(project_root),
        "lock": {
            "exists": lock.exists,
            "valid": lock.valid,
            "expired": lock.expired,
            "process_alive": lock.process_alive,
            "data": lock.data,
        },
        "inspection": inspection,
    }
    atomic_write_json(project_root / ".agent" / "EVIDENCE" / "latest-status-report.json", report)
    append_markdown(
        project_root / ".agent" / "AUTOMATION_REPORT.md",
        f"## {utc_now()} — Status report\n\n- State: `{state['status']}`\n- State valid: `{not validation_errors}`\n- Acceptance passed: `{acceptance_ok}`\n- Next action: {report['next_action']}",
    )
    return report


def archive_completed_run(project_root: Path) -> dict[str, Any]:
    state = read_json(project_root / ".agent" / "TASK_STATE.json")
    if state["status"] != "DONE":
        raise LoopError("only DONE runs may be archived")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive = project_root / ".agent" / "ARCHIVE" / timestamp
    archive.mkdir(parents=True, exist_ok=False)
    names = (
        "TASK_STATE.json",
        "TASK_PLAN.md",
        "PROGRESS.md",
        "FAILURE_LOG.md",
        "RESEARCH_LOG.md",
        "SOURCE_REGISTRY.json",
        "DECISION_LOG.md",
        "ACCEPTANCE.md",
        "AUTOMATION_REPORT.md",
        "FINAL_HANDOFF.md",
    )
    copied = []
    for name in names:
        source = project_root / ".agent" / name
        if source.exists():
            shutil.copy2(source, archive / name)
            copied.append(name)
    manifest = {"archived_at": utc_now(), "source": str(project_root.resolve()), "files": copied}
    atomic_write_json(archive / "manifest.json", manifest)
    return {"archive": str(archive), **manifest}


def update_acceptance(project_root: Path, updates: dict[str, bool]) -> dict[str, Any]:
    state_path = project_root / ".agent" / "TASK_STATE.json"
    state = read_json(state_path)
    for key, value in updates.items():
        if key not in MANDATORY_ACCEPTANCE:
            raise AcceptanceError(f"unknown mandatory acceptance item: {key}")
        if not isinstance(value, bool):
            raise AcceptanceError(f"acceptance value for {key} must be boolean")
        state.setdefault("acceptance_results", {})[key] = value
    atomic_write_json(state_path, state)
    return state


def run_once(project_root: Path, *, owner: str = "codex-automation") -> dict[str, Any]:
    state = read_json(project_root / ".agent" / "TASK_STATE.json")
    if state["status"] == "DONE":
        return {"modified": False, "state": "DONE", "action": select_next_action(state)}
    if state["status"] == "BLOCKED":
        return {"modified": False, "state": "BLOCKED", "action": select_next_action(state)}
    lock = acquire_lock(project_root, owner=owner, operation="completion-loop-run", ttl_minutes=30)
    try:
        inspection = inspect_project(project_root)
        state = read_json(project_root / ".agent" / "TASK_STATE.json")
        state["run_count"] = int(state.get("run_count", 0)) + 1
        state["last_progress_at"] = utc_now()
        state["next_action"] = select_next_action(state)
        atomic_write_json(project_root / ".agent" / "TASK_STATE.json", state)
        report = generate_status_report(project_root)
        return {"modified": True, "state": state["status"], "lock": lock, "inspection": inspection, "report": report}
    finally:
        release_lock(project_root, run_id=lock["run_id"])


def find_forbidden_command_text(paths: Iterable[Path]) -> list[dict[str, str]]:
    forbidden = (
        re.compile(r"\bgit\s+push\b"),
        re.compile(r"\bgit\s+merge\b"),
        re.compile(r"\b(?:curl|wget)\b[^\n|]*\|\s*(?:ba)?sh\b"),
        re.compile(r"\b(?:deploy|release)\s+--production\b"),
    )
    findings: list[dict[str, str]] = []
    for path in paths:
        if not path.is_file() or path.suffix not in {".py", ".sh"}:
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden:
            if pattern.search(text):
                findings.append({"path": str(path), "pattern": pattern.pattern})
    return findings
