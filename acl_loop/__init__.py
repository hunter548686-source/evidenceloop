"""EvidenceLoop public API."""

from .core import (
    ALL_STATES,
    MANDATORY_ACCEPTANCE,
    TERMINAL_STATES,
    acquire_lock,
    archive_completed_run,
    check_acceptance,
    check_source_freshness,
    default_task_state,
    detect_stalled_task,
    generate_status_report,
    inspect_project,
    install_global_skill,
    install_project,
    record_failure,
    release_lock,
    select_next_action,
    transition_state,
    uninstall,
    validate_state,
)

__all__ = [
    "ALL_STATES",
    "MANDATORY_ACCEPTANCE",
    "TERMINAL_STATES",
    "acquire_lock",
    "archive_completed_run",
    "check_acceptance",
    "check_source_freshness",
    "default_task_state",
    "detect_stalled_task",
    "generate_status_report",
    "inspect_project",
    "install_global_skill",
    "install_project",
    "record_failure",
    "release_lock",
    "select_next_action",
    "transition_state",
    "uninstall",
    "validate_state",
]

__version__ = "0.1.0"
