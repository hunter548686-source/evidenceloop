from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from . import core


def _project(value: str) -> Path:
    return Path(value).expanduser().resolve()


def _print(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="evidenceloop", description="EvidenceLoop: fail-closed evidence and conformance for coding agents")
    sub = parser.add_subparsers(dest="command", required=True)

    install_global = sub.add_parser("install-global-skill")
    install_global.add_argument("--destination-root")

    install_project = sub.add_parser("install-project")
    install_project.add_argument("--project", required=True)
    install_project.add_argument(
        "--goal",
        default="验证 EvidenceLoop 已正确安装，并建立真实、可续跑、无业务代码修改的初始治理状态。",
    )

    inspect = sub.add_parser("inspect")
    inspect.add_argument("--project", required=True)

    validate = sub.add_parser("validate-state")
    validate.add_argument("--project", required=True)

    transition = sub.add_parser("transition")
    transition.add_argument("--project", required=True)
    transition.add_argument("--to", required=True, choices=core.ALL_STATES)
    transition.add_argument("--reason", required=True)
    transition.add_argument("--next-action")
    transition.add_argument("--stop-reason")
    transition.add_argument("--accept", action="append", default=[], help="Acceptance item to set true")

    next_action = sub.add_parser("next-action")
    next_action.add_argument("--project", required=True)

    acceptance = sub.add_parser("acceptance")
    acceptance.add_argument("--project", required=True)
    acceptance.add_argument("--set", action="append", default=[], metavar="NAME=BOOL")

    freshness = sub.add_parser("source-freshness")
    freshness.add_argument("--project", required=True)
    freshness.add_argument("--max-age-days", type=int, default=30)

    stalled = sub.add_parser("stalled")
    stalled.add_argument("--project", required=True)
    stalled.add_argument("--threshold-hours", type=int, default=4)

    lock = sub.add_parser("lock")
    lock.add_argument("--project", required=True)
    lock.add_argument("action", choices=("status", "acquire", "release", "recover"))
    lock.add_argument("--owner", default="manual")
    lock.add_argument("--operation", default="manual-operation")
    lock.add_argument("--ttl-minutes", type=int, default=30)
    lock.add_argument("--run-id")

    failure = sub.add_parser("record-failure")
    failure.add_argument("--project", required=True)
    failure.add_argument("--category", required=True, choices=sorted(core.ERROR_CATEGORIES))
    failure.add_argument("--strategy", required=True)
    failure.add_argument("--error", required=True)
    failure.add_argument("--root-cause-hypothesis", required=True)
    failure.add_argument("--experiment", required=True)
    failure.add_argument("--repair", required=True)

    report = sub.add_parser("report")
    report.add_argument("--project", required=True)

    archive = sub.add_parser("archive")
    archive.add_argument("--project", required=True)

    uninstall = sub.add_parser("uninstall")
    uninstall.add_argument("--project", required=True)
    uninstall.add_argument("--keep-project-skill", action="store_true")
    uninstall.add_argument("--keep-managed-block", action="store_true")
    uninstall.add_argument("--remove-state", action="store_true")
    uninstall.add_argument("--remove-global-skill", action="store_true")
    uninstall.add_argument("--global-skill-root")

    run_once = sub.add_parser("run-once")
    run_once.add_argument("--project", required=True)
    run_once.add_argument("--owner", default="codex-automation")

    return parser


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "on", "passed"}:
        return True
    if normalized in {"false", "0", "no", "off", "failed"}:
        return False
    raise argparse.ArgumentTypeError(f"invalid boolean: {value}")


def _acceptance_updates(items: Sequence[str]) -> dict[str, bool]:
    updates: dict[str, bool] = {}
    for item in items:
        if "=" in item:
            key, raw = item.split("=", 1)
            updates[key] = _parse_bool(raw)
        else:
            updates[item] = True
    return updates


def execute(args: argparse.Namespace) -> Any:
    command = args.command
    if command == "install-global-skill":
        destination = Path(args.destination_root).expanduser() if args.destination_root else None
        return core.install_global_skill(destination)
    if command == "install-project":
        return core.install_project(_project(args.project), goal=args.goal)
    if command == "inspect":
        return core.inspect_project(_project(args.project))
    if command == "validate-state":
        errors = core.validate_state_file(_project(args.project))
        return {"ok": not errors, "errors": errors}
    if command == "transition":
        updates = {name: True for name in args.accept}
        return core.transition_state(
            _project(args.project),
            args.to,
            reason=args.reason,
            next_action=args.next_action,
            stop_reason=args.stop_reason,
            acceptance_updates=updates or None,
        )
    if command == "next-action":
        return {"next_action": core.select_next_action(_project(args.project))}
    if command == "acceptance":
        root = _project(args.project)
        if args.set:
            core.update_acceptance(root, _acceptance_updates(args.set))
        passed, missing = core.check_acceptance(root)
        return {"passed": passed, "missing": missing}
    if command == "source-freshness":
        return core.check_source_freshness(_project(args.project), args.max_age_days)
    if command == "stalled":
        return core.detect_stalled_task(_project(args.project), args.threshold_hours)
    if command == "lock":
        root = _project(args.project)
        if args.action == "status":
            status = core.lock_status(root)
            return {
                "exists": status.exists,
                "valid": status.valid,
                "expired": status.expired,
                "process_alive": status.process_alive,
                "data": status.data,
            }
        if args.action == "acquire":
            return core.acquire_lock(
                root,
                owner=args.owner,
                operation=args.operation,
                ttl_minutes=args.ttl_minutes,
                run_id=args.run_id,
            )
        if args.action == "release":
            if not args.run_id:
                raise core.LoopError("--run-id is required for lock release")
            return core.release_lock(root, run_id=args.run_id)
        return core.recover_expired_lock(root)
    if command == "record-failure":
        return core.record_failure(
            _project(args.project),
            category=args.category,
            strategy=args.strategy,
            error=args.error,
            root_cause_hypothesis=args.root_cause_hypothesis,
            experiment=args.experiment,
            repair=args.repair,
        )
    if command == "report":
        return core.generate_status_report(_project(args.project))
    if command == "archive":
        return core.archive_completed_run(_project(args.project))
    if command == "uninstall":
        return core.uninstall(
            _project(args.project),
            remove_project_skill=not args.keep_project_skill,
            remove_managed_block=not args.keep_managed_block,
            remove_state=args.remove_state,
            global_skill_root=Path(args.global_skill_root).expanduser() if args.global_skill_root else None,
            remove_global_skill=args.remove_global_skill,
        )
    if command == "run-once":
        return core.run_once(_project(args.project), owner=args.owner)
    raise core.LoopError(f"unsupported command: {command}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        result = execute(args)
    except (core.LoopError, OSError, ValueError, json.JSONDecodeError) as exc:
        _print({"ok": False, "error": type(exc).__name__, "message": str(exc)})
        return 2
    if isinstance(result, dict) and "ok" not in result:
        result = {"ok": True, **result}
    _print(result)
    return 0 if not (isinstance(result, dict) and result.get("ok") is False) else 1


def main_with_default(command: str) -> int:
    return main([command, *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
