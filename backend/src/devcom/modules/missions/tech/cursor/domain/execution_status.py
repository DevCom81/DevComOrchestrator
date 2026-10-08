from enum import StrEnum

MAX_CORRECTIONS_PER_PLAN_VERSION = 2
SANDBOX_POLICY_VERSION = "sandbox_policy_v1_lot6a"
DEFAULT_CURSOR_MODEL = "composer-2.5"
DEFAULT_CURSOR_FAST = "false"
EXECUTE_RESERVE_EUR_MICROS = 200_000  # 0.20 € ceiling reservation (not provider hard cap)


class ExecutionStatus(StrEnum):
    INTENT = "intent"
    RUNNING = "running"
    CANCEL_REQUESTED = "cancel_requested"
    FINISHED = "finished"
    CANCELLED = "cancelled"
    FAILED = "failed"
    INTERRUPTED = "interrupted"
    UNCERTAIN = "uncertain"
    CAPTURE_INCOMPLETE = "capture_incomplete"
    RETURN_READY = "return_ready"


class IntegrationStatus(StrEnum):
    PROPOSED = "proposed"
    APPLIED = "applied"
    FAILED = "failed"
