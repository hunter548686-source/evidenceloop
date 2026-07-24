#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "tests" / "results"


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc)
    stamp = started.strftime("%Y%m%dT%H%M%SZ")
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT) + os.pathsep + environment.get("PYTHONPATH", "")
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    finished = datetime.now(timezone.utc)
    temporary_manifest = RESULTS / "temporary-repositories.json"
    temp_data = []
    if temporary_manifest.exists():
        try:
            temp_data = json.loads(temporary_manifest.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            temp_data = [{"error": "temporary repository manifest could not be parsed"}]
    summary = {
        "schema_version": "1.0",
        "started_at": started.isoformat(timespec="seconds"),
        "finished_at": finished.isoformat(timespec="seconds"),
        "duration_seconds": round((finished - started).total_seconds(), 3),
        "command": command,
        "working_directory": str(ROOT),
        "python": sys.version,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "result": "PASS" if completed.returncode == 0 else "FAIL",
        "temporary_repositories": temp_data,
        "cleanup_result": "recorded by each test case in temporary-repositories.json",
    }
    json_path = RESULTS / f"test-run-{stamp}.json"
    text_path = RESULTS / f"test-run-{stamp}.txt"
    latest_json = RESULTS / "latest.json"
    latest_text = RESULTS / "latest.txt"
    json_content = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    text_content = (
        f"COMMAND: {' '.join(command)}\n"
        f"STARTED: {summary['started_at']}\n"
        f"FINISHED: {summary['finished_at']}\n"
        f"EXIT_CODE: {completed.returncode}\n"
        f"RESULT: {summary['result']}\n\n"
        f"STDOUT\n{completed.stdout}\n\nSTDERR\n{completed.stderr}\n"
    )
    for path, content in (
        (json_path, json_content),
        (latest_json, json_content),
        (text_path, text_content),
        (latest_text, text_content),
    ):
        path.write_text(content, encoding="utf-8")
    sys.stdout.write(completed.stdout)
    sys.stderr.write(completed.stderr)
    print(f"Evidence: {json_path}")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
