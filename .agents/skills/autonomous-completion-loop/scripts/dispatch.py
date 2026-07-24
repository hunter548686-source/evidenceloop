#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path


def locate_runtime() -> Path:
    configured = os.environ.get("EVIDENCELOOP_HOME") or os.environ.get("ACL_LOOP_HOME")
    candidates = [
        Path(configured).expanduser() if configured else None,
        Path.cwd(),
        Path(__file__).resolve().parents[4] if len(Path(__file__).resolve().parents) >= 5 else None,
    ]
    for candidate in candidates:
        if candidate and (candidate / "acl_loop" / "cli.py").exists():
            return candidate.resolve()
    raise SystemExit(
        "EvidenceLoop runtime not found. Install the evidenceloop package or set EVIDENCELOOP_HOME "
        "to a source checkout. ACL_LOOP_HOME remains supported for compatibility."
    )


def main() -> int:
    try:
        from acl_loop.cli import main as cli_main
    except ModuleNotFoundError:
        cli_main = None
    if cli_main is not None:
        return cli_main(sys.argv[1:])

    runtime = locate_runtime()
    sys.path.insert(0, str(runtime))
    from acl_loop.cli import main as cli_main

    return cli_main(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
